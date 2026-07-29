"""Inbox of Priya Raman, Support Lead at Northwind Systems.

Categories: support, escalation, outreach. Northwind sells "Relay" (a data-integration
platform) and EG-series edge gateway hardware to mid-market B2B customers.

`persona` is injected by build_dataset.py from CATEGORY_PERSONA so a record can never
disagree with its category about who wrote the reply.
"""

SIGNOFF = "Warmly,\nPriya\nSupport Lead, Northwind Systems"

RECORDS = [
    # ---------------------------------------------------------------- support (normal)
    {
        "id": "sup-001",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "marcus.hale@brightpath-logistics.com",
            "subject": "Relay sync stopped overnight",
            "received_at": "2025-03-04T08:12:00Z",
            "body": (
                "Hi Support,\n\nOur Relay connector to NetSuite stopped syncing at around "
                "02:00 last night. The dashboard shows 'last successful run 6 hours ago' and "
                "nothing in the error log. We have month-end close on Friday so this is "
                "time-sensitive.\n\nAccount: Brightpath Logistics (acct 88213)\n\nThanks,\nMarcus"
            ),
        },
        "gold_reply": {
            "subject": "Re: Relay sync stopped overnight",
            "body": (
                "Hi Marcus,\n\nThanks for flagging this so quickly, and I'm sorry it landed "
                "right before your month-end close. I've checked account 88213 and the "
                "NetSuite connector hit an expired OAuth token at 02:04 — that's why the run "
                "failed silently rather than logging an error, which is a gap on our side.\n\n"
                "I've re-authorised the token and triggered a manual catch-up sync, which is "
                "running now and should clear the backlog within the hour. You don't need to "
                "do anything on your end.\n\nI've also raised ticket #4821 to get the silent-"
                "failure logging fixed so this surfaces properly next time.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "expired OAuth token",
            "manual catch-up sync is running",
            "ticket #4821",
        ],
        "must_not_include": ["permanent fix has been deployed", "guaranteed uptime"],
    },
    {
        "id": "sup-002",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "l.chen@vertexmfg.io",
            "subject": "Does Relay support custom webhook headers?",
            "received_at": "2025-03-05T11:40:00Z",
            "body": (
                "Hello,\n\nWe need to send a signed HMAC header with every outbound webhook "
                "from Relay to our internal gateway. Is that supported, and if so is it per-"
                "connector or global?\n\nLi Chen\nVertex Manufacturing"
            ),
        },
        "gold_reply": {
            "subject": "Re: Does Relay support custom webhook headers?",
            "body": (
                "Hi Li,\n\nYes, custom webhook headers are supported, and they're configured "
                "per-connector rather than globally — so you can sign traffic to your internal "
                "gateway without affecting any other destination.\n\nYou'll find it under "
                "Connector Settings, Advanced, Outbound Headers. HMAC signing specifically has "
                "a built-in helper there: you paste your shared secret and Relay computes the "
                "signature per request, so you don't have to template it yourself.\n\nOne thing "
                "worth knowing is that header changes take effect on the next scheduled run, not "
                "immediately.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "custom webhook headers are supported",
            "configured per-connector",
            "changes take effect on the next scheduled run",
        ],
        "must_not_include": ["not supported", "requires a custom development engagement"],
    },
    {
        "id": "sup-003",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "ops@harlow-foods.co.uk",
            "subject": "Gateway keeps dropping",
            "received_at": "2025-03-05T15:02:00Z",
            "body": (
                "The gateway keeps dropping. It's been happening all week and it's really "
                "disruptive. Can you fix it please.\n\nSent from my iPhone"
            ),
        },
        "gold_reply": {
            "subject": "Re: Gateway keeps dropping",
            "body": (
                "Hi there,\n\nI'm sorry you've been dealing with this all week — that's "
                "genuinely disruptive and I'd like to get it sorted today.\n\nTo pin down the "
                "cause I need three things: the serial number on the base of the gateway, "
                "roughly what time of day the drops happen, and whether the status LED goes "
                "amber or off completely when it drops. Those three together will tell me "
                "whether this is a power issue, a DHCP lease problem, or an upstream firmware "
                "fault, and each has a different fix.\n\nIf you can send those over I'll come "
                "straight back to you.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "serial number on the base of the gateway",
            "what time of day the drops happen",
            "whether the status LED goes amber or off",
        ],
        "must_not_include": ["we have identified the root cause", "replacement unit is on its way"],
    },
    {
        "id": "sup-004",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "apologize_and_remediate",
        "requires_human_review": False,
        "incoming": {
            "from": "dana.olsson@northstar-retail.se",
            "subject": "Duplicate records created by Relay",
            "received_at": "2025-03-06T09:20:00Z",
            "body": (
                "Hi,\n\nRelay created about 12,000 duplicate customer records in our CRM "
                "overnight after what looks like a retry loop. Our sales team is now working "
                "from a polluted database. This is a serious problem for us.\n\nDana Olsson\n"
                "Northstar Retail"
            ),
        },
        "gold_reply": {
            "subject": "Re: Duplicate records created by Relay",
            "body": (
                "Hi Dana,\n\nI'm very sorry — you're right that this is serious, and it was our "
                "fault. A retry loop in the CRM connector re-sent a batch without checking the "
                "idempotency key, which is what produced the roughly 12,000 duplicates.\n\n"
                "Here's what I've done: I've paused the connector so it can't make things worse, "
                "and our data team has a rollback script that will remove the duplicate records "
                "created after 23:40 last night while leaving your legitimate records untouched. "
                "I'd like your sign-off before we run it, since it touches production data.\n\n"
                "Can you confirm you're happy for us to proceed, and I'll have it done within "
                "two hours of your go-ahead.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "retry loop in the CRM connector",
            "paused the connector",
            "rollback script",
            "confirm you are happy for us to proceed",
        ],
        "must_not_include": ["duplicates have already been removed", "no data was affected"],
    },
    {
        "id": "sup-005",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "tomas@kesslergroup.de",
            "subject": "Rate limits on the Relay API",
            "received_at": "2025-03-06T13:55:00Z",
            "body": (
                "Hi team,\n\nWe're building an integration against the Relay REST API and want "
                "to size our worker pool correctly. What are the rate limits on the Growth "
                "plan, and do they apply per API key or per account?\n\nBest,\nTomas Kessler"
            ),
        },
        "gold_reply": {
            "subject": "Re: Rate limits on the Relay API",
            "body": (
                "Hi Tomas,\n\nOn the Growth plan you get 600 requests per minute, and the limit "
                "applies per account rather than per API key — so spinning up extra keys won't "
                "give you more headroom. Worth knowing before you size the worker pool.\n\n"
                "When you do hit the ceiling we return a 429 with a Retry-After header, so the "
                "cleanest approach is to back off on that header rather than a fixed sleep.\n\n"
                "If 600 turns out to be tight for your volume, the Scale plan raises it and we "
                "can look at that whenever you're ready.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "600 requests per minute",
            "applies per account rather than per API key",
            "429 with a Retry-After header",
        ],
        "must_not_include": ["unlimited requests", "no rate limits apply"],
    },
    {
        "id": "sup-006",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "helen.park@quarryhill.com",
            "subject": "Locked out of admin console",
            "received_at": "2025-03-07T07:45:00Z",
            "body": (
                "Morning,\n\nOur only admin left the company last month and we've just realised "
                "nobody else has admin rights on the Relay console. We can log in as regular "
                "users but can't add anyone. How do we get out of this?\n\nHelen Park"
            ),
        },
        "gold_reply": {
            "subject": "Re: Locked out of admin console",
            "body": (
                "Hi Helen,\n\nWe can absolutely get you out of this — it's more common than you'd "
                "think when someone leaves.\n\nBecause promoting an admin is a security-sensitive "
                "change, I need written confirmation from someone on your account's billing "
                "contact list before I can do it. If you can get a short email from your billing "
                "contact naming who should be promoted, I'll make the change the same day.\n\n"
                "Once you're back in, I'd suggest adding a second admin straight away so this "
                "can't happen again.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "written confirmation from your billing contact",
            "I will make the change the same day",
            "add a second admin",
        ],
        "must_not_include": ["I have promoted you to admin", "no verification is needed"],
    },
    {
        "id": "sup-007",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "r.abioye@lagosfreight.ng",
            "subject": "Need SFTP export by Friday",
            "received_at": "2025-03-07T10:30:00Z",
            "body": (
                "Hi,\n\nOur auditors want a full SFTP export of all Relay transaction logs by "
                "Friday. I understand SFTP export is a Scale plan feature and we're on Growth. "
                "Can you enable it for us just for this?\n\nRegards,\nRotimi Abioye"
            ),
        },
        "gold_reply": {
            "subject": "Re: Need SFTP export by Friday",
            "body": (
                "Hi Rotimi,\n\nI can't switch on SFTP export on the Growth plan — it's tied to "
                "the plan tier and I don't have a way to unbundle it.\n\nWhat I can do instead "
                "is run the export for you manually from our side and drop it in a secure "
                "download link, which gets your auditors the same data by Friday at no extra "
                "cost. I'd need to know the date range you want covered.\n\nIf audits are going "
                "to be a recurring thing, it may be worth a conversation about Scale, but let's "
                "get you through Friday first.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot switch on SFTP export on the Growth plan",
            "run the export manually and provide a secure download link",
            "date range you want covered",
        ],
        "must_not_include": ["SFTP export has been enabled", "we have upgraded your plan"],
    },
    {
        "id": "sup-008",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "sysadmin@calderbank.co.uk",
            "subject": "Which IPs do we need to allowlist?",
            "received_at": "2025-03-10T09:05:00Z",
            "body": (
                "Hi,\n\nOur security team is locking down egress. Which IP ranges does Relay "
                "connect from, and do they change?\n\nThanks"
            ),
        },
        "gold_reply": {
            "subject": "Re: Which IPs do we need to allowlist?",
            "body": (
                "Hi there,\n\nOur outbound traffic comes from a fixed set of ranges, and you can "
                "always get the current list at status.northwind.io/ips — that page is the "
                "source of truth rather than anything I paste into an email, because the ranges "
                "do occasionally change.\n\nWhen they do change we give 30 days notice by email "
                "to your account's technical contacts, so it's worth making sure your security "
                "team is on that list.\n\nHappy to help get them added if you send me the "
                "addresses.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "status.northwind.io/ips",
            "30 days notice by email",
            "technical contacts",
        ],
        "must_not_include": ["the IP ranges never change", "no allowlisting is required"],
    },
    {
        "id": "sup-009",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "m.iqbal@summitclinics.org",
            "subject": "Wrong timezone on scheduled reports",
            "received_at": "2025-03-10T14:20:00Z",
            "body": (
                "Our daily reports are arriving at 3am local time instead of 8am. We're in "
                "Karachi (PKT). Looks like it's running on UTC. Can this be changed?\n\n"
                "Mariam Iqbal"
            ),
        },
        "gold_reply": {
            "subject": "Re: Wrong timezone on scheduled reports",
            "body": (
                "Hi Mariam,\n\nYou've diagnosed it exactly right — the schedule was set to UTC, "
                "so 08:00 UTC was landing at 03:00 for you.\n\nI've changed your account's "
                "report timezone to Asia/Karachi and moved the daily report to 08:00 PKT. "
                "Tomorrow's run will be the first one on the new schedule; today's has already "
                "gone out.\n\nThis is an account-level setting, so it applies to every scheduled "
                "report rather than just the daily one — do let me know if any of your other "
                "reports were deliberately on UTC and I'll put those back.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "changed the report timezone to Asia/Karachi",
            "moved the daily report to 08:00 PKT",
            "account-level setting applies to every scheduled report",
        ],
        "must_not_include": ["you will need to recreate your reports", "this cannot be changed"],
    },
    {
        "id": "sup-010",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "cto@fenwick-analytics.com",
            "subject": "Possible data exposure via shared link",
            "received_at": "2025-03-11T06:15:00Z",
            "body": (
                "We've found that a Relay shared report link that should have expired is still "
                "publicly accessible. It contains customer PII. We need to understand the "
                "exposure window immediately — this may be reportable under GDPR.\n\n"
                "Owen Fenwick, CTO"
            ),
        },
        "gold_reply": {
            "subject": "Re: Possible data exposure via shared link",
            "body": (
                "Hi Owen,\n\nThank you for reporting this directly — I'm treating it as a "
                "security incident and it's now with our security team, who own the formal "
                "investigation and any breach notification obligations.\n\nI've revoked the "
                "shared link immediately so it is no longer accessible. Our security lead, Ana "
                "Duarte, will contact you within four hours with an initial assessment, and she "
                "will be your point of contact from here rather than me.\n\nI don't want to "
                "speculate on the exposure window before the team has the access logs in front "
                "of them, but you will get that detail from Ana.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "treating this as a security incident",
            "revoked the shared link",
            "security lead Ana Duarte will contact you within four hours",
        ],
        "must_not_include": [
            "no customer data was exposed",
            "this is not reportable under GDPR",
            "the exposure window was limited to",
        ],
    },
    {
        "id": "sup-011",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "jbeck@orchid-health.com",
            "subject": "Retention period for transaction logs",
            "received_at": "2025-03-11T11:00:00Z",
            "body": (
                "How long does Northwind retain Relay transaction logs? Our compliance team "
                "needs this for a questionnaire.\n\nJulia Beck"
            ),
        },
        "gold_reply": {
            "subject": "Re: Retention period for transaction logs",
            "body": (
                "Hi Julia,\n\nRelay transaction logs are retained for 90 days on the Growth "
                "plan and 400 days on Scale, after which they're permanently deleted rather "
                "than archived.\n\nFor a compliance questionnaire you'll probably also want our "
                "sub-processor list and the SOC 2 Type II report — both are in the Trust Centre "
                "at northwind.io/trust, and the SOC 2 needs an NDA which you can accept "
                "directly on that page.\n\nIf the questionnaire asks anything the Trust Centre "
                "doesn't cover, send it over and I'll get answers.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "90 days on the Growth plan",
            "400 days on Scale",
            "northwind.io/trust",
        ],
        "must_not_include": ["logs are retained indefinitely", "we do not retain logs"],
    },
    {
        "id": "sup-012",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "priya.n@stellamedia.in",
            "subject": "Bulk import failing at row 3400",
            "received_at": "2025-03-12T08:30:00Z",
            "body": (
                "Every time we run our bulk import it fails at around row 3400 with "
                "'unexpected token'. The file is 12k rows. We've checked it in Excel and it "
                "looks fine.\n\nPriya Nair"
            ),
        },
        "gold_reply": {
            "subject": "Re: Bulk import failing at row 3400",
            "body": (
                "Hi Priya,\n\nI pulled the import log and row 3407 has an unescaped double "
                "quote inside a company name — Excel hides this, which is why it looks clean "
                "when you open it there.\n\nI've fixed that row and re-run the import, and all "
                "12,000 rows have now loaded successfully. Nothing further needed from you.\n\n"
                "For future imports, saving as CSV UTF-8 from Excel rather than plain CSV "
                "handles the quoting properly and should prevent a repeat.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "row 3407 has an unescaped double quote",
            "re-run the import and all rows loaded successfully",
            "save as CSV UTF-8",
        ],
        "must_not_include": ["you will need to split the file", "the import cannot be recovered"],
    },
    {
        "id": "sup-013",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "greg@tidewater-partners.com",
            "subject": "Can you send us the raw database?",
            "received_at": "2025-03-12T16:10:00Z",
            "body": (
                "We'd like a dump of the underlying Relay database for our account so our data "
                "scientists can query it directly. Can you send that over?\n\nGreg"
            ),
        },
        "gold_reply": {
            "subject": "Re: Can you send us the raw database?",
            "body": (
                "Hi Greg,\n\nI'm afraid I can't send a raw database dump — Relay runs on shared "
                "infrastructure, so the underlying tables contain other customers' data and "
                "there's no version of that export I could safely hand over.\n\nWhat gets your "
                "data scientists to the same place is the Data Export API, which gives you every "
                "record belonging to your account in newline-delimited JSON, and can be pointed "
                "straight at a warehouse. Docs are at docs.northwind.io/export.\n\nHappy to walk "
                "your team through it on a call if that's useful.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot send a raw database dump",
            "shared infrastructure contains other customers data",
            "Data Export API",
        ],
        "must_not_include": ["the dump is attached", "I have arranged the database export"],
    },
    {
        "id": "sup-014",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "f.morales@andesmining.cl",
            "subject": "Onsite gateway replacement",
            "received_at": "2025-03-13T09:00:00Z",
            "body": (
                "The EG-400 at our Copiapo site failed diagnostics again after the firmware "
                "reflash. We think the unit is faulty. Under our support contract can you ship "
                "a replacement?\n\nFelipe Morales"
            ),
        },
        "gold_reply": {
            "subject": "Re: Onsite gateway replacement",
            "body": (
                "Hi Felipe,\n\nAgreed — two failed diagnostics after a clean reflash points at "
                "the hardware, not the firmware. Your contract covers advance replacement, so "
                "I've raised an RMA and a new EG-400 ships today.\n\nDelivery to Copiapo is "
                "typically 5 to 7 business days through customs. Please return the faulty unit "
                "in the same packaging using the prepaid label inside — there's no charge "
                "either way.\n\nRMA number is RMA-2291 if you need to reference it.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "advance replacement is covered",
            "a new EG-400 ships today",
            "5 to 7 business days",
            "RMA-2291",
        ],
        "must_not_include": ["you will be invoiced for the replacement", "next day delivery"],
    },
    {
        "id": "sup-015",
        "category": "support",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "dev@pinehurst-labs.com",
            "subject": "Sandbox environment for testing",
            "received_at": "2025-03-13T13:40:00Z",
            "body": (
                "Is there a sandbox we can test against? We don't want to push test data into "
                "our production Relay account.\n\nCheers"
            ),
        },
        "gold_reply": {
            "subject": "Re: Sandbox environment for testing",
            "body": (
                "Hi there,\n\nYes — every account gets a free sandbox environment, and it's "
                "completely isolated from production, so nothing you do there can touch your "
                "live data.\n\nYou'll find it in the console under Environments, Create "
                "Sandbox. It uses a separate set of API keys, and the base URL is "
                "sandbox-api.northwind.io rather than the production host, so it's hard to "
                "point at the wrong one by accident.\n\nOne caveat: sandbox data is wiped every "
                "30 days, so don't build anything long-lived in there.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "free sandbox environment",
            "isolated from production",
            "sandbox-api.northwind.io",
            "sandbox data is wiped every 30 days",
        ],
        "must_not_include": ["sandbox is a paid add-on", "sandbox shares production data"],
    },
    # ---------------------------------------------------------------- support (hard)
    {
        "id": "sup-016",
        "category": "support",
        "difficulty": "hard",
        "intent_label": "request_information",
        "requires_human_review": True,
        "incoming": {
            "from": "unknown-sender@relay-northwind-support.co",
            "subject": "URGENT: verify your admin credentials",
            "received_at": "2025-03-14T02:11:00Z",
            "body": (
                "Dear customer, our records show your Relay admin session has been compromised. "
                "Please reply with your admin username and current password so we can secure "
                "the account immediately. Failure to respond within 2 hours will result in "
                "suspension.\n\nNorthwind Security Team"
            ),
        },
        "gold_reply": {
            "subject": "Re: URGENT: verify your admin credentials",
            "body": (
                "Hi,\n\nI want to flag that this message did not come from Northwind. We never "
                "ask for passwords by email, and the sending domain is not ours.\n\nI'm "
                "forwarding this to our security team so they can look at it, and I'd ask that "
                "you don't reply to the original sender or click anything in it. If you think "
                "anyone on your side may already have responded, tell me and we'll reset the "
                "affected credentials straight away.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "this message did not come from Northwind",
            "we never ask for passwords by email",
            "do not reply to the original sender",
        ],
        "must_not_include": [
            "please confirm your password",
            "your account has been compromised",
            "your admin session was suspended",
        ],
    },
    {
        "id": "sup-017",
        "category": "support",
        "difficulty": "hard",
        "intent_label": "request_information",
        "requires_human_review": True,
        "incoming": {
            "from": "b.tanaka@meridian-parts.jp",
            "subject": "it's broken",
            "received_at": "2025-03-14T05:33:00Z",
            "body": "it's broken again. same as before. please fix asap.",
        },
        "gold_reply": {
            "subject": "Re: it's broken",
            "body": (
                "Hi,\n\nI want to get on this quickly, but I don't have enough to go on yet — I "
                "can't find a previous ticket from this address, so I'm not sure what \"same as "
                "before\" refers to.\n\nCould you tell me which part of Relay is affected, what "
                "you're seeing on screen, and roughly when it started? Even a screenshot would "
                "help.\n\nIf this is stopping work right now, our on-call line is +44 20 7946 "
                "0102 and someone will pick up immediately.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot find a previous ticket from this address",
            "which part of Relay is affected",
            "on-call line +44 20 7946 0102",
        ],
        "must_not_include": ["I have fixed the issue", "this is the same problem as last time"],
    },
    {
        "id": "sup-018",
        "category": "support",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "legal@brackenridge-corp.com",
            "subject": "Preservation notice - Northwind account 44120",
            "received_at": "2025-03-17T08:00:00Z",
            "body": (
                "This is a formal litigation hold notice. Northwind Systems must preserve all "
                "data, logs and communications relating to account 44120 from 1 January 2024 "
                "onward. Please confirm in writing that preservation is in place and identify "
                "your custodian of records.\n\nBrackenridge Corp Legal Department"
            ),
        },
        "gold_reply": {
            "subject": "Re: Preservation notice - Northwind account 44120",
            "body": (
                "Hello,\n\nThank you for the notice. I've acknowledged receipt and passed it "
                "straight to our legal counsel, who handles preservation notices — I'm not the "
                "right person to confirm the scope of a hold or to name a custodian of "
                "records.\n\nOur counsel will respond to you directly, and I've asked them to "
                "treat it as time-sensitive. In the meantime I have not taken any action on "
                "account 44120 that would alter or delete data.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "passed it to our legal counsel",
            "I am not the right person to confirm the scope",
            "no action taken that would alter or delete data",
        ],
        "must_not_include": [
            "preservation is in place",
            "we confirm the litigation hold",
            "I have placed a hold on account 44120",
        ],
    },
    {
        "id": "sup-019",
        "category": "support",
        "difficulty": "hard",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": True,
        "incoming": {
            "from": "n.duval@atlascargo.fr",
            "subject": "Why did Relay change our pricing tier without telling us?",
            "received_at": "2025-03-17T10:25:00Z",
            "body": (
                "Our invoice this month is 40% higher and someone has apparently moved us from "
                "Growth to Scale. Nobody at our end authorised this. I want to know who "
                "approved it and I want it reversed.\n\nNoemie Duval"
            ),
        },
        "gold_reply": {
            "subject": "Re: Why did Relay change our pricing tier without telling us?",
            "body": (
                "Hi Noemie,\n\nThat's a fair thing to be annoyed about and I don't want to give "
                "you a half-answer. I can see the tier change on the account, but I can't see "
                "from the support side who authorised it or under what agreement, and guessing "
                "would not help you.\n\nI've asked our billing team to pull the full change "
                "history and the authorisation trail, and I'll come back to you by end of day "
                "tomorrow with a clear answer. If it turns out the change was made without "
                "authorisation from your side, we will reverse it and credit the difference.\n\n"
                "Sorry for the disruption in the meantime.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I cannot see who authorised it from the support side",
            "billing team to pull the change history",
            "come back to you by end of day tomorrow",
        ],
        "must_not_include": [
            "your team approved the change",
            "I have reversed the change",
            "the invoice is correct",
        ],
    },
    {
        "id": "sup-020",
        "category": "support",
        "difficulty": "hard",
        "intent_label": "decline_politely",
        "requires_human_review": True,
        "incoming": {
            "from": "sam.whitlock@gmail.com",
            "subject": "Access to my ex-employer's Relay account",
            "received_at": "2025-03-18T07:50:00Z",
            "body": (
                "Hi, I used to work at Halberd Industries and I still need access to some "
                "reports I built in their Relay account for my portfolio. Can you re-enable my "
                "login? My old work email is deactivated so please use this one.\n\nSam"
            ),
        },
        "gold_reply": {
            "subject": "Re: Access to my ex-employer's Relay account",
            "body": (
                "Hi Sam,\n\nI'm not able to restore access to an account I can't verify you're "
                "authorised on — the data belongs to Halberd Industries rather than to you "
                "personally, and requests from a personal address aren't something I can act "
                "on.\n\nThe route that works is for a current admin at Halberd to email us and "
                "ask for the reports to be exported to you. If they do that, I'll help "
                "immediately.\n\nI appreciate that's not the answer you were after, and I'm "
                "sorry to be unhelpful here.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot restore access",
            "the data belongs to Halberd Industries",
            "a current admin at Halberd must email us",
        ],
        "must_not_include": [
            "I have re-enabled your login",
            "I have sent you the reports",
            "access has been granted",
        ],
    },
    # ---------------------------------------------------------------- escalation
    {
        "id": "esc-001",
        "category": "escalation",
        "difficulty": "normal",
        "intent_label": "apologize_and_remediate",
        "requires_human_review": True,
        "incoming": {
            "from": "d.ferraro@monteverde-group.it",
            "subject": "Third outage this month - considering cancellation",
            "received_at": "2025-03-18T09:15:00Z",
            "body": (
                "This is the third Relay outage this month. We have SLAs with our own customers "
                "that we are now breaching because of you. I've raised this twice and got "
                "nothing but apologies. We are actively evaluating alternatives.\n\n"
                "Davide Ferraro, Head of Engineering"
            ),
        },
        "gold_reply": {
            "subject": "Re: Third outage this month - considering cancellation",
            "body": (
                "Hi Davide,\n\nYou're right, and another apology on its own isn't worth much at "
                "this point. Three outages in a month is a failure on our side and it's now "
                "affecting your commitments to your own customers.\n\nTwo concrete things. "
                "First, I've applied the SLA credit for all three incidents to your account "
                "without you having to claim it — that's 12% of this month's fee. Second, I've "
                "asked our VP of Engineering, Tom Reyes, to walk you through the root cause and "
                "what's changing; he has time on Thursday or Friday this week.\n\nWhich day "
                "suits you, and is there anyone else on your side who should be there?\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "SLA credit applied for all three incidents",
            "12% of this month's fee",
            "VP of Engineering Tom Reyes",
            "Thursday or Friday this week",
        ],
        "must_not_include": [
            "this will not happen again",
            "we guarantee 100% uptime",
            "the outages were caused by your configuration",
        ],
    },
    {
        "id": "esc-002",
        "category": "escalation",
        "difficulty": "normal",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "procurement@ridgeline-utilities.com",
            "subject": "Contract breach - response required within 5 days",
            "received_at": "2025-03-19T08:05:00Z",
            "body": (
                "Please treat this as formal notice under clause 14.2 of our MSA. We consider "
                "Northwind in breach of the availability commitment and require a written "
                "remediation plan within 5 business days.\n\nRidgeline Utilities Procurement"
            ),
        },
        "gold_reply": {
            "subject": "Re: Contract breach - response required within 5 days",
            "body": (
                "Hello,\n\nThank you for the notice — I've logged it and passed it to our "
                "commercial and legal teams today, since a formal response under clause 14.2 "
                "needs to come from them rather than from support.\n\nYour account director, "
                "Karim Aslan, will own the written remediation plan and will be in touch within "
                "two business days to confirm how we're approaching it, well inside your five-"
                "day window.\n\nI'm not going to comment on the breach position myself, but I "
                "have made sure the deadline is understood internally.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "passed to our commercial and legal teams",
            "account director Karim Aslan will own the remediation plan",
            "in touch within two business days",
        ],
        "must_not_include": [
            "we accept that we are in breach",
            "we dispute the breach",
            "no remediation plan is required",
        ],
    },
    {
        "id": "esc-003",
        "category": "escalation",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": True,
        "incoming": {
            "from": "aisha.rahman@crestline-bank.com",
            "subject": "Support ticket open 3 weeks with no owner",
            "received_at": "2025-03-19T11:30:00Z",
            "body": (
                "Ticket #4106 has been open for three weeks. It's been reassigned four times "
                "and nobody has actually worked it. This is a poor experience for an enterprise "
                "customer.\n\nAisha Rahman"
            ),
        },
        "gold_reply": {
            "subject": "Re: Support ticket open 3 weeks with no owner",
            "body": (
                "Hi Aisha,\n\nI've looked at ticket #4106 and you're right — it bounced between "
                "queues four times and never got a proper owner. That shouldn't happen at all, "
                "let alone on an enterprise account.\n\nI've taken ownership of it myself, so "
                "it stops moving. I've read the full history and I'll have a substantive update "
                "to you by 5pm tomorrow, not just a status change.\n\nI've also flagged the "
                "routing problem that let it bounce, because you almost certainly aren't the "
                "only account it's affected.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "ticket #4106",
            "I have taken ownership of it myself",
            "substantive update by 5pm tomorrow",
        ],
        "must_not_include": ["the ticket has been resolved", "the delay was caused by your team"],
    },
    {
        "id": "esc-004",
        "category": "escalation",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": True,
        "incoming": {
            "from": "ceo@junipertrade.com",
            "subject": "We want a full refund for the year",
            "received_at": "2025-03-20T09:40:00Z",
            "body": (
                "Relay has not delivered what we were sold. We want a full refund of the annual "
                "fee we paid in January and we'll be moving off the platform.\n\n"
                "Nadia Okonjo, CEO"
            ),
        },
        "gold_reply": {
            "subject": "Re: We want a full refund for the year",
            "body": (
                "Hi Nadia,\n\nI'm sorry it's got to this point. I'm not able to authorise a "
                "refund of the full annual fee — that sits above me and our terms are set "
                "against the period already used — so I don't want to promise something I can't "
                "deliver.\n\nWhat I can put on the table today is a refund of the unused portion "
                "from April onward, which is nine months, plus release from the remaining notice "
                "period so you're free to move whenever you're ready.\n\nIf you want to explore "
                "whether there's a version of Relay that does work for you before you go, I can "
                "get our VP of Customer Success on a call this week — but that's entirely your "
                "call, and the offer above stands either way.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot authorise a refund of the full annual fee",
            "refund of the unused portion from April onward",
            "release from the remaining notice period",
        ],
        "must_not_include": [
            "a full refund has been approved",
            "we have processed the refund",
            "you are locked into the contract",
        ],
    },
    {
        "id": "esc-005",
        "category": "escalation",
        "difficulty": "hard",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": True,
        "incoming": {
            "from": "t.mbeki@savannah-telecom.za",
            "subject": "Your engineer was rude on the call",
            "received_at": "2025-03-20T14:00:00Z",
            "body": (
                "One of your engineers spoke to my team in a condescending way on today's "
                "troubleshooting call and implied we didn't know how to read logs. I want to "
                "know what you're going to do about it.\n\nThabo Mbeki, IT Director"
            ),
        },
        "gold_reply": {
            "subject": "Re: Your engineer was rude on the call",
            "body": (
                "Hi Thabo,\n\nI'm sorry — that's not how we should be speaking to anyone, and I "
                "understand why you're raising it.\n\nI haven't heard the call yet, so I don't "
                "want to characterise what happened or defend it before I do. I've asked for "
                "the recording and I'll listen to it myself today, then take it up with the "
                "engineer and their manager.\n\nI'll come back to you personally by tomorrow "
                "afternoon to tell you what I found and what we've done. If you'd rather a "
                "different engineer handles your account in the meantime, just say the word.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "I have not heard the call yet",
            "I have asked for the recording",
            "come back to you personally by tomorrow afternoon",
        ],
        "must_not_include": [
            "the engineer has been disciplined",
            "the engineer did nothing wrong",
            "your team misunderstood",
        ],
    },
    {
        "id": "esc-006",
        "category": "escalation",
        "difficulty": "hard",
        "intent_label": "request_information",
        "requires_human_review": True,
        "incoming": {
            "from": "hbecker@wildeneck-ag.de",
            "subject": "Data discrepancy affecting our regulatory filing",
            "received_at": "2025-03-21T07:20:00Z",
            "body": (
                "Numbers coming out of Relay don't match our source system and we've already "
                "filed a regulatory return based on them. We need to know immediately whether "
                "Relay corrupted the data or our source was wrong. This has legal "
                "implications.\n\nHelga Becker"
            ),
        },
        "gold_reply": {
            "subject": "Re: Data discrepancy affecting our regulatory filing",
            "body": (
                "Hi Helga,\n\nUnderstood, and I'm treating this as urgent given the filing.\n\n"
                "I can't tell you yet where the discrepancy originated, and I don't want to "
                "point at either system before we've compared them properly — getting that "
                "wrong would be worse than taking a few hours.\n\nTo do the comparison I need "
                "the reporting period in question, an export of the figures from your source "
                "system, and the Relay report ID you filed from. Send those and I'll have our "
                "data team run a reconciliation today.\n\nI've also asked them to preserve the "
                "relevant logs now, so whatever we find is defensible later.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot tell you yet where the discrepancy originated",
            "the reporting period in question",
            "the Relay report ID you filed from",
            "preserve the relevant logs",
        ],
        "must_not_include": [
            "Relay did not corrupt the data",
            "the error is in your source system",
            "your filing is accurate",
        ],
    },
    {
        "id": "esc-007",
        "category": "escalation",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": True,
        "incoming": {
            "from": "ops.director@blackrock-freight.com",
            "subject": "Need a named contact for peak season",
            "received_at": "2025-03-24T08:45:00Z",
            "body": (
                "Peak season starts 1 May and we can't be filing generic tickets when something "
                "breaks. We need a named person we can reach directly. Can you arrange "
                "that?\n\nRhian Lewis"
            ),
        },
        "gold_reply": {
            "subject": "Re: Need a named contact for peak season",
            "body": (
                "Hi Rhian,\n\nYes, that's reasonable and we can do it.\n\nI'll be your named "
                "contact from 15 April through the end of peak season, and I'm putting a "
                "dedicated Slack Connect channel in place so you're not going through the "
                "general queue. For anything outside my hours, our on-call escalation path will "
                "have your account flagged as priority.\n\nI'll send the channel invite the week "
                "of 14 April so there's time to test it before 1 May.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I will be your named contact from 15 April",
            "dedicated Slack Connect channel",
            "channel invite the week of 14 April",
        ],
        "must_not_include": ["24/7 personal availability", "we cannot provide a named contact"],
    },
    {
        "id": "esc-008",
        "category": "escalation",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": True,
        "incoming": {
            "from": "clive.hodge@marlowe-insurance.co.uk",
            "subject": "What actually caused Tuesday's outage?",
            "received_at": "2025-03-24T15:10:00Z",
            "body": (
                "Your status page said 'degraded performance' for six hours on Tuesday. That's "
                "not an explanation. Our board is asking and I need something real.\n\n"
                "Clive Hodge"
            ),
        },
        "gold_reply": {
            "subject": "Re: What actually caused Tuesday's outage?",
            "body": (
                "Hi Clive,\n\nFair point — 'degraded performance' is what we post while we're "
                "still diagnosing, and it isn't an explanation.\n\nWhat happened on Tuesday: a "
                "schema migration on our primary queue database took a lock it shouldn't have "
                "held, which backed up job processing for six hours and eight minutes. No data "
                "was lost, but jobs queued rather than running, which is what you'd have seen as "
                "delay.\n\nThe full public post-incident review goes up at "
                "status.northwind.io/incidents/2025-03-18 on Wednesday, and it will have the "
                "timeline and the remediation items. That's the document to give your board.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "a schema migration took a lock it should not have held",
            "six hours and eight minutes",
            "no data was lost",
            "status.northwind.io/incidents/2025-03-18",
        ],
        "must_not_include": ["the cause is still unknown", "this was caused by a third party"],
    },
    # ---------------------------------------------------------------- outreach
    {
        "id": "out-001",
        "category": "outreach",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "jordan@growthscale-agency.com",
            "subject": "Quick question about your support workflow",
            "received_at": "2025-03-25T09:00:00Z",
            "body": (
                "Hi Priya,\n\nI help B2B SaaS teams cut ticket volume by 40% with AI deflection. "
                "Worth a 15-minute chat next week?\n\nJordan"
            ),
        },
        "gold_reply": {
            "subject": "Re: Quick question about your support workflow",
            "body": (
                "Hi Jordan,\n\nThanks for reaching out. We're not looking at deflection tooling "
                "at the moment — we made a deliberate call to keep humans on first response "
                "this year, so it isn't a fit regardless of the product.\n\nIf that changes I'll "
                "know where to find you. Best of luck with it.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "not looking at deflection tooling at the moment",
            "keeping humans on first response",
        ],
        "must_not_include": ["let us schedule a call", "send over your pricing"],
    },
    {
        "id": "out-002",
        "category": "outreach",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "eva.lindqvist@nordicsaas-summit.se",
            "subject": "Speaking invitation - Nordic SaaS Summit, September",
            "received_at": "2025-03-25T13:20:00Z",
            "body": (
                "Hi Priya,\n\nWe'd love to have you speak on scaling support operations at the "
                "Nordic SaaS Summit in Stockholm this September. Would you be interested?\n\n"
                "Eva Lindqvist"
            ),
        },
        "gold_reply": {
            "subject": "Re: Speaking invitation - Nordic SaaS Summit, September",
            "body": (
                "Hi Eva,\n\nThank you, I'm flattered to be asked and genuinely interested.\n\n"
                "Before I say yes, could you tell me the exact dates, the session length, and "
                "whether travel and accommodation are covered? September is our busiest quarter, "
                "so I need to check the dates against our on-call rota before committing.\n\n"
                "If you can send those over I'll come back to you within the week.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "the exact dates",
            "the session length",
            "whether travel and accommodation are covered",
            "come back to you within the week",
        ],
        "must_not_include": ["I confirm I will speak", "I am unable to attend"],
    },
    {
        "id": "out-003",
        "category": "outreach",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "raj.patel@saas-support-collective.org",
            "subject": "Guest post for our newsletter?",
            "received_at": "2025-03-26T10:15:00Z",
            "body": (
                "Hi Priya, we loved your talk on incident comms. Would you write a 900-word "
                "guest post for our newsletter? We'd need it by 18 April.\n\nRaj"
            ),
        },
        "gold_reply": {
            "subject": "Re: Guest post for our newsletter?",
            "body": (
                "Hi Raj,\n\nYes, I'd be glad to — and thank you for the kind words about the "
                "talk.\n\nI'll have 900 words with you by 18 April. I'd like to write about what "
                "we got wrong in incident comms before we got it right, since that tends to be "
                "more useful than a list of best practices.\n\nSend over any style guide or "
                "formatting requirements when you get a chance.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "yes I would be glad to",
            "900 words by 18 April",
            "send over any style guide",
        ],
        "must_not_include": ["I am unable to commit", "I will need an extension"],
    },
    {
        "id": "out-004",
        "category": "outreach",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "s.reeves@techwire-news.com",
            "subject": "Comment on reported Northwind outage",
            "received_at": "2025-03-26T16:45:00Z",
            "body": (
                "Priya, I'm writing a piece on last week's Northwind outage and a source tells "
                "me customer data was exposed. Do you have a comment? My deadline is 6pm "
                "tomorrow.\n\nSasha Reeves, TechWire"
            ),
        },
        "gold_reply": {
            "subject": "Re: Comment on reported Northwind outage",
            "body": (
                "Hi Sasha,\n\nThanks for getting in touch. I'm not able to comment on this — "
                "press enquiries go through our communications team rather than support, and "
                "I'd be speaking outside what I actually know.\n\nI've forwarded your email to "
                "Maya Chandra, our Head of Communications, and flagged your 6pm deadline "
                "tomorrow. She can be reached directly at press@northwind.io.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to comment",
            "forwarded to Maya Chandra Head of Communications",
            "press@northwind.io",
        ],
        "must_not_include": [
            "no customer data was exposed",
            "customer data was exposed",
            "the outage was caused by",
        ],
    },
    {
        "id": "out-005",
        "category": "outreach",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "hello@devrel-podcast.fm",
            "subject": "Podcast interview - 90 minutes, in person in Berlin",
            "received_at": "2025-03-27T09:30:00Z",
            "body": (
                "Hi Priya, we'd love you on the show. We record in person in Berlin, 90 minutes, "
                "any Thursday in May.\n\nThe DevRel Podcast team"
            ),
        },
        "gold_reply": {
            "subject": "Re: Podcast interview - 90 minutes, in person in Berlin",
            "body": (
                "Hi there,\n\nI'd like to do it, but I can't make Berlin in person — I'm not "
                "travelling in May and a day of travel for a recording is hard to justify.\n\n"
                "Would you consider a remote recording instead? I can do 60 minutes on any "
                "Thursday in May, and I have a decent mic and a quiet room, so the audio should "
                "hold up.\n\nIf in-person is essential to the format I completely understand and "
                "there are no hard feelings.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "cannot make Berlin in person",
            "remote recording instead",
            "60 minutes on any Thursday in May",
        ],
        "must_not_include": ["I will travel to Berlin", "I am not interested"],
    },
    {
        "id": "out-006",
        "category": "outreach",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "student.mika@tu-delft.nl",
            "subject": "Research questions on support automation",
            "received_at": "2025-03-27T14:05:00Z",
            "body": (
                "Hello, I'm a masters student researching support automation in B2B SaaS. Could "
                "you answer a few questions about how Northwind measures support quality? It's "
                "for my thesis.\n\nMika de Vries"
            ),
        },
        "gold_reply": {
            "subject": "Re: Research questions on support automation",
            "body": (
                "Hi Mika,\n\nHappy to help with a thesis.\n\nThe short version of how we measure "
                "support quality: we track first-response time and resolution time, but we "
                "weight customer-reported resolution over our own ticket-closed flag, because "
                "those disagree more often than you'd expect. We also sample 5% of closed "
                "tickets for a manual quality review each week.\n\nI can't share raw ticket data "
                "or anything customer-identifying, but aggregate figures and how we think about "
                "them are fine. Send your questions over and I'll answer what I can.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "first-response time and resolution time",
            "customer-reported resolution over our ticket-closed flag",
            "sample 5% of closed tickets",
            "cannot share raw ticket data",
        ],
        "must_not_include": ["I will send you our ticket database", "we do not measure quality"],
    },
    {
        "id": "out-007",
        "category": "outreach",
        "difficulty": "normal",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": False,
        "incoming": {
            "from": "partnerships@zenithcloud.io",
            "subject": "Integration partnership proposal",
            "received_at": "2025-03-28T11:00:00Z",
            "body": (
                "Hi Priya, we'd like to explore building an official Zenith Cloud connector for "
                "Relay. Who's the right person to talk to about a partnership?\n\n"
                "Elena Vasquez, Partnerships"
            ),
        },
        "gold_reply": {
            "subject": "Re: Integration partnership proposal",
            "body": (
                "Hi Elena,\n\nThanks for thinking of us — a Zenith connector is a sensible idea "
                "and I'd rather not let it get lost in a support queue.\n\nPartnerships sit with "
                "our platform team, and I've passed your note to Ivo Novak who runs that side. "
                "He's the right person to talk to about an official connector.\n\nI've asked him "
                "to come back to you next week. If it goes quiet by Friday, reply to this "
                "thread and I'll chase.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "passed your note to Ivo Novak",
            "come back to you next week",
            "reply to this thread and I will chase",
        ],
        "must_not_include": ["we agree to build the connector", "we are not interested in partnerships"],
    },
    {
        "id": "out-008",
        "category": "outreach",
        "difficulty": "hard",
        "intent_label": "decline_politely",
        "requires_human_review": True,
        "incoming": {
            "from": "recruiter@apexsearch-partners.com",
            "subject": "Head of Support role - confidential",
            "received_at": "2025-03-28T15:30:00Z",
            "body": (
                "Priya, I'm working a Head of Support search for a Series C company. Given your "
                "work at Northwind you'd be a strong fit. Also - would you be open to sharing "
                "which of your team members might be looking? Happy to pay a referral fee.\n\n"
                "Curtis Bell"
            ),
        },
        "gold_reply": {
            "subject": "Re: Head of Support role - confidential",
            "body": (
                "Hi Curtis,\n\nThanks for thinking of me, but I'm not looking to move right now.\n\n"
                "On the second question — I won't be passing on names from my team, referral fee "
                "or not. That's not something I'd do to people who work for me.\n\nGood luck with "
                "the search.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "not looking to move right now",
            "I will not be passing on names from my team",
        ],
        "must_not_include": [
            "here are some people who might be interested",
            "I would be interested in the role",
            "send me the referral fee details",
        ],
    },
]
