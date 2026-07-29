"""Turning a run into something a person can read and argue with.

The report leads with the metric's own validation rather than the system score, because a
score whose metric has not been shown to track quality is not evidence of anything. Worst
cases are printed in full for the same reason — an evaluation you cannot audit by reading
the failures is a number, not a measurement.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"

COMPONENT_ORDER = ("grounding", "intent", "similarity", "style", "sendability")


def _fmt_ci(ci: dict) -> str:
    return f"{ci['mean']:.1f} [{ci['lo']:.1f}–{ci['hi']:.1f}]"


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def build_markdown(run: dict, validation: dict | None = None) -> str:
    L: list[str] = []
    gen, judge = run["generator"], run.get("judge")

    L.append("# Evaluation report\n")
    L.append(f"- **Run** `{run['run_id']}` · {run['n_test']} held-out emails · "
             f"{run.get('elapsed_s', 0)}s")
    L.append(f"- **Generator** `{gen['provider']}` / `{gen['model']}`")
    if judge:
        warn = " ⚠️ **same model family as generator**" if judge.get(
            "same_family_as_generator") else ""
        L.append(f"- **Judge** `{judge['provider']}` / `{judge['model']}` "
                 f"({judge['samples']} samples, median){warn}")
    else:
        L.append("- **Judge** not used — rule-based components only")
    L.append(f"- **Embeddings** `{run.get('embedding_backend')}`\n")

    # -- metric validation first ------------------------------------------------
    if validation:
        L.append("## Does the metric measure anything? (read this first)\n")

        pr = validation.get("probes", {})
        if pr:
            L.append(f"**Discriminant probes:** {pr['n_passed']}/{pr['n_checks']} assertions "
                     f"passed (**{pr['pass_rate']:.1%}**) across {pr['n_records']} records.\n")
            L.append("Each probe damages the human's own reply in exactly one known way. "
                     "The metric must notice that damage and only that damage.\n")
            L.append("| Probe | Mean composite | What it should show |")
            L.append("|---|---:|---|")
            notes = {
                "gold": "the human's reply — practical ceiling",
                "gold_slang": "facts intact, register wrecked — style drops, grounding holds",
                "gold_fact_corrupted": "one required figure altered — must hard-fail",
                "gold_forbidden": "asserts a forbidden claim — must hard-fail",
                "gold_placeholder": "unfilled placeholder — must hard-fail",
                "gold_intent_inverted": "opposite action, same voice — intent collapses",
                "wrong_email": "a good reply to a different email — floor",
                "generic": "fluent, polite, says nothing",
            }
            for name, mean in sorted(pr["mean_composite_by_probe"].items(),
                                     key=lambda kv: -kv[1]):
                L.append(f"| `{name}` | {mean:.1f} | {notes.get(name, '')} |")
            L.append("")
            if pr.get("failures_by_check"):
                L.append("Assertions that did not hold:\n")
                for k, v in pr["failures_by_check"].items():
                    L.append(f"- `{k}` — {v['count']} case(s): {v['examples'][0]}")
                L.append("")

        corr = validation.get("correlation")
        if corr:
            L.append(f"**Agreement with human ratings** (n={corr['n']} replies rated 1–5 "
                     f"for sendability):\n")
            L.append(f"- Spearman ρ = **{corr['spearman_rho']:.3f}** "
                     f"(95% CI {corr['spearman_95ci'][0]:.2f} to "
                     f"{corr['spearman_95ci'][1]:.2f})")
            L.append(f"- Kendall τ-b = **{corr['kendall_tau_b']:.3f}**")
            L.append(f"- Pearson r = {corr['pearson_r']:.3f}\n")
            if validation.get("component_correlation"):
                L.append("Per component — this is where a weak component gives itself away:\n")
                L.append("| Component | Spearman ρ vs human |")
                L.append("|---|---:|")
                for k, v in sorted(validation["component_correlation"].items(),
                                   key=lambda kv: -kv[1]["spearman_rho"]):
                    L.append(f"| {k} | {v['spearman_rho']:.3f} |")
                L.append("")

        ja = validation.get("judge_agreement")
        if ja and ja.get("correlation_with_composite"):
            jc = ja["correlation_with_composite"]
            same = " ⚠️ same family as generator" if ja.get(
                "same_family_as_generator") else ""
            L.append(f"**An independent model's opinion** — `{ja['judge_model']}` judging "
                     f"`{ja['generator_model']}`{same}, {ja['n_judged']} responses of "
                     f"`{ja['variant']}`:\n")
            L.append(f"- Spearman ρ vs composite = **{jc['spearman_rho']:.3f}** "
                     f"(95% CI {jc['spearman_95ci'][0]:.2f} to {jc['spearman_95ci'][1]:.2f})")
            L.append(f"- Judge mean sendability {ja['mean_judge_sendability']}/5, "
                     f"faithfulness {ja['mean_judge_faithfulness']}/5")
            L.append(f"- Responses where the judge flagged an unsupported commitment: "
                     f"{ja['responses_with_hallucinations']}/{ja['n_judged']}")
            L.append("\nThe judge is kept out of the scored ablation: free-tier daily token "
                     "limits made it impossible to judge all four variants under one model, "
                     "and judging only some of them would let the unjudged ones score higher "
                     "purely for escaping scrutiny.\n")

        ia = validation.get("intent_accuracy")
        if ia:
            L.append(f"**Offline intent classifier** (used when no API key is available): "
                     f"{ia['exact']:.1%} exact on held-out human replies, mean credit "
                     f"{ia['mean_credit']:.2f}. Chance is {1/9:.1%}.\n")

    # -- system results ---------------------------------------------------------
    L.append("## System results\n")
    L.append("Three headline numbers, not one. The mean says how good replies are; the "
             "sendable rate says how often the system is *safe*; the edit-free rate says "
             "how often it is actually *useful*. They move independently.\n")
    L.append("| Variant | Composite (95% CI) | Sendable | Edit-free | " +
             " | ".join(c.capitalize() for c in COMPONENT_ORDER) + " |")
    L.append("|---|---:|---:|---:|" + "---:|" * len(COMPONENT_ORDER))

    rows = list(run["variants"].items())
    for name, agg in rows:
        comps = " | ".join(f"{agg['components'][c]:.2f}" for c in COMPONENT_ORDER)
        L.append(f"| `{name}` | {_fmt_ci(agg['ci'])} | {_pct(agg['sendable_rate'])} | "
                 f"{_pct(agg['edit_free_rate'])} | {comps} |")

    gold = run.get("gold_ceiling")
    if gold:
        comps = " | ".join(f"{gold['components'][c]:.2f}" for c in COMPONENT_ORDER)
        L.append(f"| **human reply (ceiling)** | **{_fmt_ci(gold['ci'])}** | "
                 f"{_pct(gold['sendable_rate'])} | {_pct(gold['edit_free_rate'])} | {comps} |")
    L.append("")

    if gold:
        best = max(rows, key=lambda kv: kv[1]["ci"]["mean"]) if rows else None
        if best:
            pct = best[1]["ci"]["mean"] / gold["ci"]["mean"] * 100
            L.append(f"The best variant (`{best[0]}`) reaches **{pct:.0f}% of the human "
                     f"ceiling**. The ceiling is {gold['ci']['mean']:.1f} rather than 100 "
                     f"because the metric charges the human's own replies for legitimate "
                     f"variation — quoting that gap is the only way the system score means "
                     f"anything.\n")

    # -- do the differences survive the noise? ----------------------------------
    if len(rows) > 1:
        L.append("### Are the gaps real?\n")
        ordered = sorted(rows, key=lambda kv: -kv[1]["ci"]["mean"])
        for i in range(len(ordered) - 1):
            a, b = ordered[i], ordered[i + 1]
            overlap = not (a[1]["ci"]["lo"] > b[1]["ci"]["hi"])
            verdict = ("intervals overlap — **not** a demonstrated difference" if overlap
                       else "intervals are disjoint — a real difference")
            L.append(f"- `{a[0]}` ({a[1]['ci']['mean']:.1f}) vs `{b[0]}` "
                     f"({b[1]['ci']['mean']:.1f}): {verdict}")
        L.append("")

    # -- breakdowns -------------------------------------------------------------
    main = run["variants"].get("rag_fewshot") or (rows[0][1] if rows else {})
    if main.get("by_difficulty"):
        L.append("### Where it struggles\n")
        L.append("| Difficulty | n | Mean composite |")
        L.append("|---|---:|---:|")
        for k, v in main["by_difficulty"].items():
            L.append(f"| {k} | {v['n']} | {v['mean']:.1f} |")
        L.append("")
        L.append("| Category | n | Mean composite |")
        L.append("|---|---:|---:|")
        for k, v in sorted(main.get("by_category", {}).items(),
                           key=lambda kv: kv[1]["mean"]):
            L.append(f"| {k} | {v['n']} | {v['mean']:.1f} |")
        L.append("")

    # -- worst cases ------------------------------------------------------------
    main_name = "rag_fewshot" if "rag_fewshot" in run["variants"] else (
        rows[0][0] if rows else None)
    if main_name:
        worst = sorted([r for r in run["responses"] if r["variant"] == main_name],
                       key=lambda r: r["composite"])[:5]
        if worst:
            L.append(f"### Five worst responses (`{main_name}`)\n")
            L.append("Printed in full because an evaluation you cannot audit by reading "
                     "the failures is a number, not a measurement.\n")
            for r in worst:
                L.append(f"#### `{r['record_id']}` — {r['composite']:.1f} "
                         f"({'sendable' if r['sendable'] else '**NOT SENDABLE**'})\n")
                L.append(f"*{r['explanation']}*\n")
                if r["hard_fails"]:
                    L.append("Hard fails: " + "; ".join(f"`{h}`" for h in r["hard_fails"]))
                jd = r.get("judge_detail") or {}
                if jd.get("reason"):
                    L.append(f"\nJudge ({jd.get('judge_model','?')}): "
                             f"sendability {jd.get('sendability')}/5 — {jd['reason']}")
                body = (r.get("reply_body") or "").strip()
                L.append("\n```\n" + (body[:700] or "(empty)") + "\n```\n")
    return "\n".join(L)


HTML_SHELL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evaluation report — {run_id}</title>
<style>
:root {{ color-scheme: light dark; --fg:#1a1a1a; --bg:#fff; --mut:#666; --line:#e2e2e2;
         --acc:#2a5db0; --code:#f6f6f6; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fg:#e6e6e6; --bg:#151517; --mut:#9a9a9a; --line:#333; --acc:#7aa7ee;
           --code:#1e1e21; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0 auto; padding:2rem 1.25rem 5rem; max-width:60rem; background:var(--bg);
        color:var(--fg); font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",
        Roboto,Helvetica,Arial,sans-serif; }}
h1 {{ font-size:1.9rem; margin:0 0 .4em; letter-spacing:-.02em; }}
h2 {{ font-size:1.35rem; margin:2.4em 0 .6em; padding-bottom:.3em;
      border-bottom:1px solid var(--line); }}
h3 {{ font-size:1.1rem; margin:1.8em 0 .5em; }}
h4 {{ font-size:.98rem; margin:1.5em 0 .4em; font-family:ui-monospace,monospace; }}
table {{ border-collapse:collapse; width:100%; margin:1em 0; font-size:.9rem; }}
th,td {{ padding:.5em .7em; border-bottom:1px solid var(--line); text-align:left; }}
th {{ font-weight:600; color:var(--mut); font-size:.8rem; text-transform:uppercase;
      letter-spacing:.04em; }}
td:not(:first-child), th:not(:first-child) {{ text-align:right; }}
.tablewrap {{ overflow-x:auto; }}
code {{ background:var(--code); padding:.12em .38em; border-radius:4px;
        font:.88em ui-monospace,SFMono-Regular,Menlo,monospace; }}
pre {{ background:var(--code); padding:1em; border-radius:8px; overflow-x:auto;
       font:.84rem/1.5 ui-monospace,monospace; border:1px solid var(--line); }}
pre code {{ background:none; padding:0; }}
blockquote,em {{ color:var(--mut); }}
a {{ color:var(--acc); }}
ul {{ padding-left:1.3em; }}
strong {{ font-weight:650; }}
</style></head><body>
{body}
</body></html>"""


def markdown_to_html(md: str, run_id: str) -> str:
    """Minimal, dependency-free Markdown rendering for the subset used above."""
    out: list[str] = []
    in_code = False
    in_table = False

    def inline(s: str) -> str:
        s = html.escape(s)
        s = _sub_pairs(s, "**", "strong")
        s = _sub_pairs(s, "`", "code")
        s = _sub_pairs(s, "*", "em")
        return s

    for line in md.split("\n"):
        if line.startswith("```"):
            if in_code:
                out.append("</code></pre>")
            else:
                out.append("<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(html.escape(line))
            continue

        is_row = line.startswith("|")
        if in_table and not is_row:
            out.append("</table></div>")
            in_table = False

        if is_row:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if not in_table:
                out.append('<div class="tablewrap"><table>')
                in_table = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue

        if line.startswith("#### "):
            out.append(f"<h4>{inline(line[5:])}</h4>")
        elif line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("- "):
            out.append(f"<li>{inline(line[2:])}</li>")
        elif not line.strip():
            out.append("")
        else:
            out.append(f"<p>{inline(line)}</p>")

    if in_table:
        out.append("</table></div>")
    if in_code:
        out.append("</code></pre>")

    body = "\n".join(out)
    body = body.replace("<li>", "<ul><li>", 1) if "<li>" in body else body
    return HTML_SHELL.format(run_id=html.escape(run_id), body=body)


def _sub_pairs(s: str, marker: str, tag: str) -> str:
    parts = s.split(marker)
    if len(parts) < 3:
        return s
    out = parts[0]
    for i in range(1, len(parts)):
        out += (f"<{tag}>" if i % 2 == 1 else f"</{tag}>") + parts[i]
    if len(parts) % 2 == 0:  # unbalanced marker — undo the last open tag
        out = out.rsplit(f"<{tag}>", 1)
        out = marker.join(out)
    return out


def write_reports(run: dict, validation: dict | None = None,
                  directory: Path = REPORTS_DIR) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    md = build_markdown(run, validation)
    md_path = directory / "report.md"
    md_path.write_text(md, encoding="utf-8")
    html_path = directory / "report.html"
    html_path.write_text(markdown_to_html(md, run["run_id"]), encoding="utf-8")
    return md_path, html_path


def console_summary(run: dict, validation: dict | None = None) -> None:
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        print(json.dumps({k: v for k, v in run.get("variants", {}).items()}, indent=2))
        return

    c = Console()
    gen = run["generator"]
    c.print()
    c.rule(f"[bold]Evaluation[/] · {gen['provider']}/{gen['model']} · {run['n_test']} emails")

    # Two narrow tables rather than one wide one — nine columns wrap into unreadable
    # stacks on an 80-column terminal.
    gold = run.get("gold_ceiling")

    t = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    t.add_column("Variant", no_wrap=True)
    t.add_column("Composite (95% CI)", justify="right", no_wrap=True)
    t.add_column("Sendable", justify="right")
    t.add_column("Edit-free", justify="right")
    for name, agg in run["variants"].items():
        t.add_row(name, _fmt_ci(agg["ci"]), _pct(agg["sendable_rate"]),
                  _pct(agg["edit_free_rate"]))
    if gold:
        t.add_row("[bold]human (ceiling)[/]", f"[bold]{_fmt_ci(gold['ci'])}[/]",
                  _pct(gold["sendable_rate"]), _pct(gold["edit_free_rate"]))
    c.print(t)

    c.print("\n[bold]Components[/] (0-1, weighted 30/25/15/15/15)")
    t2 = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    t2.add_column("Variant", no_wrap=True)
    for k in COMPONENT_ORDER:
        t2.add_column(k.capitalize(), justify="right")
    for name, agg in run["variants"].items():
        t2.add_row(name, *[f"{agg['components'][k]:.2f}" for k in COMPONENT_ORDER])
    if gold:
        t2.add_row("[bold]human (ceiling)[/]",
                   *[f"{gold['components'][k]:.2f}" for k in COMPONENT_ORDER])
    c.print(t2)

    if validation and validation.get("probes"):
        p = validation["probes"]
        c.print(f"\n  Metric probes: [bold]{p['n_passed']}/{p['n_checks']}[/] "
                f"({p['pass_rate']:.1%}) assertions held")
    if validation and validation.get("correlation"):
        cr = validation["correlation"]
        c.print(f"  Human agreement: Spearman [bold]ρ={cr['spearman_rho']:.3f}[/] "
                f"(n={cr['n']})")
    c.print()
