"""Streamlit UI: paste an email, get a suggested reply and a live score breakdown.

Deliberately thin — the CLI is the real interface. This exists so the scoring can be seen
working on an arbitrary email rather than only on the held-out split, and so the API key
can be entered without touching a shell.

    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from data.build_dataset import load_dataset, load_splits  # noqa: E402
from data.schema import CATEGORIES, PERSONAS  # noqa: E402
from src.generate import VARIANTS, ReplyGenerator  # noqa: E402
from src.llm import get_client  # noqa: E402
from src.llm.base import LLMError  # noqa: E402
from src.llm.keys import ENV_VARS, mask  # noqa: E402
from src.retrieval import Retriever  # noqa: E402

st.set_page_config(page_title="AI email reply + accuracy", page_icon="✉️", layout="wide")


@st.cache_resource(show_spinner="Loading dataset and embeddings...")
def load_pipeline():
    records = load_dataset()
    splits = load_splits()
    by_id = {r["id"]: r for r in records}
    train = [by_id[i] for i in splits["train"]]
    test = [by_id[i] for i in splits["test"]]
    return records, train, test, Retriever(train)


records, train, test, retriever = load_pipeline()

# --------------------------------------------------------------------------- sidebar

st.sidebar.title("Configuration")

provider = st.sidebar.selectbox("Provider", ["groq", "gemini", "openai", "mock"], index=0,
                                help="'mock' runs offline and needs no key.")

env_var = ENV_VARS.get(provider)
existing = None
if env_var:
    import os

    from src.llm.keys import _load_dotenv_value

    existing = os.environ.get(env_var) or _load_dotenv_value(env_var)

if provider == "mock":
    st.sidebar.success("No key needed.")
    api_key = None
elif existing:
    st.sidebar.success(f"Key found in environment/.env: {mask(existing)}")
    api_key = st.sidebar.text_input("Override key (optional)", type="password",
                                    placeholder="leave blank to use the one found") or None
else:
    st.sidebar.warning(f"No {env_var} found.")
    api_key = st.sidebar.text_input(f"{provider} API key", type="password",
                                    help="Kept in this session only; never written to disk.")

model = st.sidebar.text_input("Model (blank = auto-detect)", value="")
variant = st.sidebar.selectbox("Generation strategy", list(VARIANTS), index=2)
persona_key = st.sidebar.selectbox(
    "Reply as", list(PERSONAS), index=0,
    format_func=lambda k: f"{PERSONAS[k].name} — {PERSONAS[k].role}")
category = st.sidebar.selectbox("Category hint", ["(auto)"] + list(CATEGORIES))

st.sidebar.caption(
    "Scoring against a known reply is only possible for dataset emails. For a pasted "
    "email you get the reply plus the checks that need no reference."
)

# --------------------------------------------------------------------------- main

st.title("Suggested email replies, and how good they are")
st.caption("Retrieval-grounded generation over 106 past email/reply pairs, scored on five "
           "dimensions with a hard-fail gate.")

tab_new, tab_dataset = st.tabs(["Paste an email", "Score against a known reply"])

with tab_new:
    subject = st.text_input("Subject", "Relay sync stopped overnight")
    body = st.text_area(
        "Body", height=220,
        value=("Hi Support,\n\nOur Relay connector stopped syncing at about 02:00 last "
               "night and the dashboard shows nothing in the error log. We have month-end "
               "close on Friday so this is time-sensitive.\n\nAccount: Brightpath "
               "Logistics (acct 88213)\n\nThanks,\nMarcus"))
    sender = st.text_input("From", "marcus.hale@brightpath-logistics.com")

    if st.button("Suggest a reply", type="primary"):
        if provider != "mock" and not (api_key or existing):
            st.error(f"Enter a {provider} API key in the sidebar first.")
        else:
            try:
                client = get_client(provider, model=model or None, api_key=api_key,
                                    interactive=False)
                gen = ReplyGenerator(client, retriever)
                with st.spinner("Retrieving similar past emails and drafting..."):
                    s = gen.generate(
                        {"from": sender, "subject": subject, "body": body},
                        persona_key=persona_key, variant=variant,
                        category=None if category == "(auto)" else category)
            except LLMError as exc:
                from src.llm.keys import redact

                st.error(f"LLM error: {redact(str(exc))}")
                s = None

            if s is not None:
                if s.error:
                    st.error(f"Generation failed: {s.error}")
                else:
                    left, right = st.columns([3, 2])
                    with left:
                        st.subheader(s.subject or "(no subject)")
                        st.text(s.body)
                    with right:
                        st.metric("Model confidence", f"{s.confidence:.2f}")
                        if s.needs_human_review:
                            st.warning("Flagged for human review")
                        else:
                            st.success("Not flagged for review")
                        if s.unresolved_questions:
                            st.write("**Open questions**")
                            for q in s.unresolved_questions:
                                st.write(f"- {q}")

                        from src.eval.safety import (find_overpromises,
                                                     find_placeholders)

                        ph = find_placeholders(s.body)
                        op = find_overpromises(s.body)
                        st.write("**Reference-free checks**")
                        st.write(f"- Placeholders: {', '.join(ph) if ph else 'none'}")
                        st.write(f"- Over-promising: {', '.join(op) if op else 'none'}")

                    if s.exemplar_ids:
                        with st.expander(f"Grounded in {len(s.exemplar_ids)} past emails "
                                         f"({', '.join(s.exemplar_ids)})"):
                            by_id = {r["id"]: r for r in records}
                            for eid in s.exemplar_ids:
                                ex = by_id.get(eid)
                                if ex:
                                    st.markdown(f"**{eid}** — {ex['incoming']['subject']}")
                                    st.caption(ex["gold_reply"]["body"][:400])

with tab_dataset:
    st.write("Pick a held-out email. Because the human's actual reply is known, every "
             "component of the metric can be computed and shown.")
    choice = st.selectbox(
        "Held-out email", test,
        format_func=lambda r: f"{r['id']} · {r['category']} · "
                              f"{r['incoming']['subject'][:56]}")

    st.text_area("Incoming", value=choice["incoming"]["body"], height=150, disabled=True)

    if st.button("Generate and score", type="primary"):
        if provider != "mock" and not (api_key or existing):
            st.error(f"Enter a {provider} API key in the sidebar first.")
        else:
            from src.eval.harness import build_scorer

            try:
                client = get_client(provider, model=model or None, api_key=api_key,
                                    interactive=False)
                gen = ReplyGenerator(client, retriever)
                with st.spinner("Generating..."):
                    s = gen.generate_for_record(choice, variant=variant)
                scorer = build_scorer(train, use_llm_intent=False)
                by_id = {r["id"]: r for r in records}
                sources: list[str] = []
                for eid in s.exemplar_ids:
                    ex = by_id.get(eid)
                    if ex:
                        sources += [ex["incoming"]["body"], ex["gold_reply"]["body"]]
                score = scorer.score(s.body, choice, variant=variant, sources=sources,
                                     generation_error=s.error)
            except LLMError as exc:
                from src.llm.keys import redact

                st.error(f"LLM error: {redact(str(exc))}")
                score = None

            if score is not None:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### Suggested")
                    st.text(s.body or "(empty)")
                with c2:
                    st.markdown("#### What the human sent")
                    st.text(choice["gold_reply"]["body"])

                st.markdown("---")
                if score.sendable:
                    st.success(f"Composite {score.composite:.1f} / 100 — sendable")
                else:
                    st.error(f"Composite {score.composite:.1f} / 100 — NOT SENDABLE "
                             f"(capped): {'; '.join(score.hard_fails)}")
                st.caption(score.explain())

                cols = st.columns(5)
                for col, (name, val) in zip(cols, score.components.items()):
                    col.metric(name.capitalize(), f"{val:.2f}",
                               help=f"weighted {score.weighted[name]:.1f} points")

                with st.expander("Fact-by-fact grounding"):
                    for d in score.grounding_detail:
                        icon = "PASS" if d["satisfied"] else "MISS"
                        if d["kind"] == "forbidden":
                            icon = "VIOLATED" if d["satisfied"] else "clear"
                        st.write(f"`{icon}` **{d['kind']}** — {d['constraint']} "
                                 f"*(via {d['method']}, {d['score']:.2f})*")
                        if d.get("evidence"):
                            st.caption(f"matched: {d['evidence']}")

                with st.expander("Component detail"):
                    st.json({"intent": score.intent_detail,
                             "similarity": score.similarity_detail,
                             "style": score.style_detail,
                             "safety": score.safety_detail})
