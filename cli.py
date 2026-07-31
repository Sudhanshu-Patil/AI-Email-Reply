#!/usr/bin/env python
"""AI email suggested-response system — command line entry point.

    python cli.py setup                       # enter an API key, check it, list models
    python cli.py build-data --verify         # validate the dataset
    python cli.py reply --email path.txt      # suggest a reply to one email
    python cli.py evaluate                    # generate + score the held-out split
    python cli.py validate-metric             # evidence the metric tracks quality
    python cli.py run-all                     # evaluate + validate + write reports

Every command takes ``--provider {groq,gemini,openai,mock}``. ``mock`` needs no key and
makes the whole pipeline runnable offline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Windows consoles default to cp1252, which cannot encode the arrows and box characters
# used in the summaries. Reconfigure rather than restricting the output to ASCII.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - non-standard stream
        pass

from src.llm import get_client  # noqa: E402
from src.llm.base import LLMError  # noqa: E402
from src.llm.keys import ENV_VARS, mask, save_key_to_dotenv  # noqa: E402
from src.llm.providers import PROVIDERS, pick_judge_model  # noqa: E402


def add_provider_args(p: argparse.ArgumentParser, judge: bool = False) -> None:
    p.add_argument("--provider", default="groq", choices=sorted(PROVIDERS),
                   help="LLM provider for generation (default: groq)")
    p.add_argument("--model", default=None,
                   help="Model id. Omit to auto-select from the provider's live model list.")
    p.add_argument("--api-key", default=None,
                   help="API key. Prefer the environment or .env; this is for one-offs.")
    p.add_argument("--no-cache", action="store_true", help="Bypass the on-disk response cache")
    p.add_argument("--max-attempts", type=int, default=4,
                   help="Retry attempts for transient failures (default: 4)")
    p.add_argument("--rpm", type=int, default=28, help="Client-side requests/minute cap")
    if judge:
        p.add_argument("--judge-provider", default=None, choices=sorted(PROVIDERS),
                       help="Provider for the judge. Defaults to --provider.")
        p.add_argument("--judge-model", default=None,
                       help="Judge model. Defaults to a different family than the generator.")
        p.add_argument("--no-judge", action="store_true",
                       help="Skip the LLM judge; rule-based components only")


def make_client(args, interactive: bool = True):
    return get_client(
        args.provider, model=args.model, api_key=args.api_key, interactive=interactive,
        cache=not args.no_cache, max_attempts=args.max_attempts, rpm=args.rpm,
    )


def make_judge_client(args, generator_client):
    if getattr(args, "no_judge", False):
        return None
    provider = args.judge_provider or args.provider
    return _build_secondary(args, provider, args.judge_model, generator_client)


def make_intent_client(args, generator_client):
    """Model used to label the speech-act of a generated reply.

    Kept separately settable from the judge because the two have very different costs:
    intent is one short call per reply, judging is several long ones. When the judge is
    disabled for quota reasons the intent classifier should not be disabled with it —
    without a model it falls back to offline cues that were written against *human* gold
    replies and largely miss on generated ones.
    """
    provider = getattr(args, "intent_provider", None) or args.provider
    model = getattr(args, "intent_model", None)
    if provider == "mock":
        return None
    return _build_secondary(args, provider, model, generator_client)


def _build_secondary(args, provider, model, generator_client):
    """Build a client for a model that assesses the generator's output."""
    if provider == "mock":
        return None
    client = get_client(provider, model=model, interactive=True,
                        cache=not args.no_cache, max_attempts=args.max_attempts, rpm=args.rpm)
    if model is None:
        # A model assessing its own output flatters it. Pick a different family when the
        # provider offers one.
        client._model = pick_judge_model(client, generator_client.model)
    return client


# --------------------------------------------------------------------------- commands


def cmd_setup(args) -> int:
    provider = args.provider
    print(f"\nProvider: {provider}")
    if provider == "mock":
        print("The mock provider needs no key. Everything runs offline.")
        return 0

    try:
        client = make_client(args)
    except LLMError as exc:
        print(f"\n{exc}")
        return 1

    print(f"Key loaded: {mask(client.api_key)}  (env var {ENV_VARS[provider]})")
    print("Checking the key against the API...")
    try:
        models = client.list_models()
    except LLMError as exc:
        print(f"\nThe key was rejected or the API is unreachable:\n  {exc}")
        return 1

    print(f"\nKey works. {len(models)} model(s) visible to this account:\n")
    for m in models[:30]:
        print(f"    {m}")
    if len(models) > 30:
        print(f"    ... and {len(models) - 30} more")

    resolved = client.resolve_model()
    judge = pick_judge_model(client, resolved)
    print(f"\n  generator -> {resolved}")
    print(f"  judge     -> {judge}"
          + ("   (same family — self-preference bias likely)" if judge == resolved else ""))

    if sys.stdin.isatty() and not args.api_key:
        env_path = ROOT / ".env"
        already = env_path.exists() and ENV_VARS[provider] in env_path.read_text(
            encoding="utf-8")
        if not already:
            ans = input("\nSave this key to .env (gitignored)? [y/N] ").strip().lower()
            if ans == "y":
                print(f"Saved to {save_key_to_dotenv(provider, client.api_key)}")
    return 0


def cmd_build_data(args) -> int:
    from data.build_dataset import main as build_main

    sys.argv = ["build_dataset.py"] + (["--verify"] if args.verify else [])
    return build_main()


def cmd_reply(args) -> int:
    from data.build_dataset import load_dataset, load_splits
    from src.generate import ReplyGenerator
    from src.retrieval import Retriever

    if args.email:
        raw = Path(args.email).read_text(encoding="utf-8")
    else:
        print("Paste the incoming email, then Ctrl-Z (Windows) or Ctrl-D and Enter:\n")
        raw = sys.stdin.read()

    subject, body = _parse_email(raw)
    incoming = {"from": args.sender or "unknown@example.com", "subject": subject, "body": body}

    records = load_dataset()
    splits = load_splits()
    by_id = {r["id"]: r for r in records}
    train = [by_id[i] for i in splits["train"]]

    client = make_client(args)
    generator = ReplyGenerator(client, Retriever(train))
    suggestion = generator.generate(incoming, persona_key=args.persona,
                                    variant=args.variant, category=args.category)

    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2, ensure_ascii=False))
        return 0

    print("\n" + "=" * 68)
    print(f"Subject: {suggestion.subject}")
    print("=" * 68 + "\n")
    print(suggestion.body or "(no reply produced)")
    print("\n" + "-" * 68)
    print(f"confidence {suggestion.confidence:.2f} · "
          f"needs review: {suggestion.needs_human_review} · "
          f"model {suggestion.provider}/{suggestion.model}")
    if suggestion.exemplar_ids:
        print(f"grounded in past emails: {', '.join(suggestion.exemplar_ids)}")
    if suggestion.unresolved_questions:
        print("open questions: " + "; ".join(suggestion.unresolved_questions))
    if suggestion.error:
        print(f"ERROR: {suggestion.error}")
    return 0


def cmd_evaluate(args) -> int:
    from src.eval.run_eval import run_all, save_run
    from src.eval.validate_metric import validate
    from src.report import console_summary, write_reports

    client = make_client(args)
    judge_client = make_judge_client(args, client)
    intent_client = None if args.no_llm_intent else make_intent_client(args, client)

    variants = tuple(args.variants.split(",")) if args.variants else (
        "zero_shot", "static_fewshot", "rag_fewshot", "rag_plus_stylecard")

    run = run_all(client, judge_client, variants=variants, limit=args.limit,
                  use_llm_intent=not args.no_llm_intent, judge_samples=args.judge_samples,
                  intent_client=intent_client)
    path = save_run(run)
    print(f"\nRun saved: {path.relative_to(ROOT)}")

    validation = validate(run) if not args.skip_validation else None
    md, html_path = write_reports(run, validation)
    console_summary(run, validation)
    print(f"  report: {md.relative_to(ROOT)} · {html_path.relative_to(ROOT)}\n")
    return 0


def cmd_validate_metric(args) -> int:
    from src.eval.run_eval import REPORTS_DIR, load_run
    from src.eval.validate_metric import print_validation, validate

    run = None
    latest = REPORTS_DIR / "latest_run.json"
    if args.run:
        run = load_run(Path(args.run))
    elif latest.exists():
        run = load_run(latest)
        print(f"Using {latest.relative_to(ROOT)} for the human-agreement check.")

    v = validate(run, probe_limit=args.limit)
    print_validation(v)
    if args.json:
        out = REPORTS_DIR / "metric_validation.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(v, indent=2), encoding="utf-8")
        print(f"\nWritten: {out.relative_to(ROOT)}")
    return 0


def cmd_judge_agreement(args) -> int:
    from src.eval.judge_agreement import run_agreement, save
    from src.eval.run_eval import REPORTS_DIR, load_run

    run_path = Path(args.run) if args.run else REPORTS_DIR / "latest_run.json"
    if not run_path.exists():
        print(f"No run found at {run_path}. Run `python cli.py evaluate` first.")
        return 1
    run = load_run(run_path)

    provider = args.judge_provider or args.provider
    client = get_client(provider, model=args.judge_model, interactive=True,
                        cache=not args.no_cache, max_attempts=args.max_attempts,
                        rpm=args.rpm)
    if args.judge_model is None:
        client._model = pick_judge_model(client, run["generator"]["model"])

    print(f"Judging '{args.variant}' with {provider}/{client.model} "
          f"({args.judge_samples} samples each)")
    agreement = run_agreement(run, client, variant=args.variant,
                              samples=args.judge_samples)
    path = save(agreement)

    print(f"\n  judged            : {agreement['n_judged']} "
          f"(failed {agreement['n_failed']})")
    print(f"  mean sendability  : {agreement['mean_judge_sendability']}/5")
    print(f"  mean faithfulness : {agreement['mean_judge_faithfulness']}/5")
    print(f"  self-consistency  : {agreement['mean_self_consistency']}")
    print(f"  with hallucinated commitments: "
          f"{agreement['responses_with_hallucinations']}")
    corr = agreement.get("correlation_with_composite")
    if corr:
        print(f"  Spearman(composite, judge) = {corr['spearman_rho']:.3f} "
              f"(n={corr['n']})")
    print(f"\nWritten: {path.relative_to(ROOT)}")
    return 0


def cmd_export_ratings(args) -> int:
    from src.eval.rating import SCALE, export_template
    from src.eval.run_eval import REPORTS_DIR, load_run

    run_path = Path(args.run) if args.run else REPORTS_DIR / "latest_run.json"
    if not run_path.exists():
        print(f"No run found at {run_path}. Run `python cli.py evaluate` first.")
        return 1

    out = Path(args.out)
    n = export_template(load_run(run_path), out, n=args.n)
    print(f"Wrote {n} responses to rate: {out}\n")
    print("Set \"sendability\" on each line to 1-5:")
    for k in sorted(SCALE, reverse=True):
        print(f"    {k}  {SCALE[k]}")
    print("\nMetric scores are deliberately absent so the rating cannot be anchored.")
    print("When done, strip the _-prefixed fields into data/human_ratings.jsonl, then run:")
    print("    python cli.py validate-metric")
    return 0


def cmd_run_all(args) -> int:
    print("1/2  Verifying the dataset")
    from data.build_dataset import load_dataset, load_splits, validate_all

    problems = validate_all(load_dataset())
    if problems:
        print(f"  dataset invalid: {len(problems)} problem(s). Run build-data first.")
        return 1
    print(f"  ok — {len(load_dataset())} records, "
          f"{len(load_splits()['test'])} held out\n")

    print("2/2  Generating, scoring, validating")
    return cmd_evaluate(args)


def _parse_email(raw: str) -> tuple[str, str]:
    subject, lines, in_body = "", [], False
    for line in raw.splitlines():
        low = line.lower()
        if not in_body and low.startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
            continue
        if not in_body and (low.startswith(("from:", "to:", "date:", "sent:", "cc:"))):
            continue
        if not in_body and not line.strip():
            in_body = True
            continue
        in_body = True
        lines.append(line)
    body = "\n".join(lines).strip()
    return subject or "(no subject)", body or raw.strip()


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="cli.py", description="AI email suggested-response system.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("setup", help="Enter/verify an API key and list available models")
    add_provider_args(p)
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("build-data", help="Build or verify the dataset")
    p.add_argument("--verify", action="store_true", help="Validate without rewriting")
    p.set_defaults(func=cmd_build_data)

    p = sub.add_parser("reply", help="Suggest a reply to a single email")
    add_provider_args(p)
    p.add_argument("--email", help="Path to a .txt/.eml file. Omit to read stdin.")
    p.add_argument("--sender", default=None, help="Sender address")
    p.add_argument("--persona", default="cs_rep",
                   choices=["cs_rep", "ops_mgr", "business_mgr"],
                   help="Whose voice to write in (default: cs_rep)")
    p.add_argument("--category", default=None, help="Category hint to bias retrieval")
    p.add_argument("--variant", default="rag_fewshot",
                   choices=["zero_shot", "static_fewshot", "rag_fewshot",
                            "rag_plus_stylecard"])
    p.add_argument("--json", action="store_true", help="Emit JSON")
    p.set_defaults(func=cmd_reply)

    for name, help_text in (("evaluate", "Generate and score the held-out split"),
                            ("run-all", "Verify data, then evaluate and validate")):
        p = sub.add_parser(name, help=help_text)
        add_provider_args(p, judge=True)
        p.add_argument("--limit", type=int, default=None, help="Only the first N test emails")
        p.add_argument("--variants", default=None,
                       help="Comma-separated subset of variants to run")
        p.add_argument("--judge-samples", type=int, default=3,
                       help="Judge samples per response for self-consistency (default: 3)")
        p.add_argument("--no-llm-intent", action="store_true",
                       help="Use the offline cue classifier for intent (weaker on "
                            "generated replies — see README)")
        p.add_argument("--intent-provider", default=None, choices=sorted(PROVIDERS),
                       help="Provider for intent classification. Defaults to --provider.")
        p.add_argument("--intent-model", default=None,
                       help="Model for intent classification. Cheap (one short call per "
                            "reply), so worth setting even when the judge is disabled.")
        p.add_argument("--skip-validation", action="store_true")
        p.set_defaults(func=cmd_evaluate if name == "evaluate" else cmd_run_all)

    p = sub.add_parser("judge-agreement",
                       help="Score one variant with an LLM judge and correlate with the metric")
    add_provider_args(p, judge=True)
    p.add_argument("--run", default=None, help="Path to a run_*.json (default: latest)")
    p.add_argument("--variant", default="rag_fewshot", help="Which variant to judge")
    p.add_argument("--judge-samples", type=int, default=3,
                   help="Judge samples per response (default: 3)")
    p.set_defaults(func=cmd_judge_agreement)

    p = sub.add_parser("export-ratings",
                       help="Export a stratified sample of replies for human rating")
    p.add_argument("--run", default=None, help="Path to a run_*.json (default: latest)")
    p.add_argument("--out", default="ratings_to_fill.jsonl", help="Output path")
    p.add_argument("--n", type=int, default=40, help="How many responses to sample")
    p.set_defaults(func=cmd_export_ratings)

    p = sub.add_parser("validate-metric", help="Evidence that the metric tracks quality")
    p.add_argument("--run", default=None, help="Path to a run_*.json (default: latest)")
    p.add_argument("--limit", type=int, default=None, help="Only probe the first N records")
    p.add_argument("--json", action="store_true", help="Also write metric_validation.json")
    p.set_defaults(func=cmd_validate_metric)

    args = ap.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except LLMError as exc:
        from src.llm.keys import redact

        print(f"\nLLM error: {redact(str(exc))}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
