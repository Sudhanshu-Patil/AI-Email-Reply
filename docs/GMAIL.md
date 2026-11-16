# Running it on a real Gmail inbox

```bash
python cli.py gmail-mine                    # your sent replies -> retrieval corpus
python cli.py gmail-draft --dry-run         # see what it would draft, no LLM call
python cli.py gmail-draft --provider groq   # create reply drafts in Gmail
```

**The valuable half is the mining, not the plumbing.** Every thread where someone wrote to
you and you replied *is* an (incoming, reply) pair — the exact shape this system retrieves
over. Pointing it at a real mailbox therefore fixes the single biggest weakness in the
project: that the shipped corpus is synthetic. `gmail-mine` walks your threads, pairs each
of your replies with the message immediately before it, strips quoted chains and signature
blocks, and writes records in the same schema `data/emails.jsonl` uses. Everything
downstream then works unchanged, and the reply voice is fitted from *your* past replies
rather than one of the three fictional personas.

## It cannot send

The OAuth scopes requested are `gmail.readonly` and `gmail.compose` — **not** `gmail.send`,
not `gmail.modify`, not full access. `gmail.compose` can create a draft and cannot
transmit it. So "this tool will never send mail on your behalf" is enforced by the
permission you grant, not by the code behaving well, and there is a test asserting the
send scope is never requested. Drafts land in the correct thread (`In-Reply-To` and
`References` are set, since `threadId` alone leaves them detached) for you to read and send.

## What the metric can and cannot tell you online

This is the honest catch. Grounding, intent-match and similarity are all measured *against
a known-correct reply*, and new mail has none. What survives at inference time is the
reference-free half — placeholders, fabricated identifiers, over-promising language, and
whether the draft defers or commits — and a placeholder or an unsourced reference number
**blocks the draft** rather than merely scoring it down (`--force` overrides).

The full five-dimension metric still applies to your mail *offline*: run it over mined
history, where your past reply is the gold answer. Grounding needs `must_include` /
`must_not_include`, which cannot be derived automatically — the practical route is to have
a model propose them from your own replies and review the list, which is far quicker than
authoring from scratch.

## Setup and privacy

One-time: create a project at `console.cloud.google.com`, enable the Gmail API, create an
OAuth client ID of type **Desktop app**, and save the JSON as `credentials.json` in the
repo root. It and the cached `.gmail_token.json` are gitignored.

Your mail is sent to whichever LLM provider you configure — the incoming message plus the
retrieved examples from your own mailbox. That is a real disclosure and the reason
`--dry-run` exists: it shows which past replies would be retrieved for each message and
creates nothing, without any content leaving your machine.
