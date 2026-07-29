"""Inbox of Dan Whitfield, Operations Manager at Northwind Systems.

Categories: scheduling, internal, vendor. Deliberately the tersest of the three personas —
short replies, decision first, bullets for anything with moving parts. This is the persona
that catches a generator which pads every reply with warmth regardless of who is writing.
"""

SIGNOFF = "- Dan"

RECORDS = [
    # ---------------------------------------------------------------- scheduling
    {
        "id": "sch-001",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "claire.dunbar@meridian-parts.com",
            "subject": "Quarterly business review - date options",
            "received_at": "2025-04-01T08:30:00Z",
            "body": (
                "Hi Dan,\n\nCan we lock in the QBR? I've got 14, 15 or 22 April free, ideally "
                "morning. 90 minutes should do it.\n\nClaire"
            ),
        },
        "gold_reply": {
            "subject": "Re: Quarterly business review - date options",
            "body": (
                "Claire -\n\n22 April, 10:00, 90 minutes. Invite sent.\n\n14 and 15 clash with "
                "our release freeze so I'd be half in the room.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["22 April at 10:00", "90 minutes", "invite sent",
                         "14 and 15 clash with our release freeze"],
        "must_not_include": ["I am available on 14 April", "let me check and get back to you"],
    },
    {
        "id": "sch-002",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "raoul.dias@caldera-systems.pt",
            "subject": "Onsite next Tuesday?",
            "received_at": "2025-04-01T11:15:00Z",
            "body": (
                "Dan - could your team come onsite next Tuesday to walk through the gateway "
                "rollout? Full day would be ideal.\n\nRaoul"
            ),
        },
        "gold_reply": {
            "subject": "Re: Onsite next Tuesday?",
            "body": (
                "Raoul -\n\nTuesday doesn't work, we're two people short that week.\n\n"
                "Options:\n- Thursday 10th, full day onsite\n- Tuesday as planned but remote, "
                "half day\n\nThursday is the better outcome. Your call.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["Tuesday does not work", "Thursday 10th full day onsite",
                         "Tuesday remote half day"],
        "must_not_include": ["we will be onsite on Tuesday", "we cannot help with the rollout"],
    },
    {
        "id": "sch-003",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "events@saasops-forum.com",
            "subject": "Panel slot - 9 May",
            "received_at": "2025-04-02T09:00:00Z",
            "body": "Dan, we've got a panel slot on ops tooling on 9 May. Interested?",
        },
        "gold_reply": {
            "subject": "Re: Panel slot - 9 May",
            "body": (
                "Thanks, but no - 9 May is our peak migration window and I'll be on call.\n\n"
                "Try me for the autumn event.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["9 May is our peak migration window", "try me for the autumn event"],
        "must_not_include": ["I will take the panel slot", "I am free on 9 May"],
    },
    {
        "id": "sch-004",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "priya.shah@velocitylabs.in",
            "subject": "Meeting",
            "received_at": "2025-04-02T13:45:00Z",
            "body": "Can we meet this week to discuss the thing we talked about? Thanks.",
        },
        "gold_reply": {
            "subject": "Re: Meeting",
            "body": (
                "Priya -\n\nHappy to, but I need two things first: what the topic is, and who "
                "else needs to be there.\n\nMy Wednesday and Friday afternoons are open.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": ["what the topic is", "who else needs to be there",
                         "Wednesday and Friday afternoons are open"],
        "must_not_include": ["I have booked the meeting", "I know what this is about"],
    },
    {
        "id": "sch-005",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "facilities@westbrook-house.co.uk",
            "subject": "Server room access - Saturday maintenance",
            "received_at": "2025-04-03T07:50:00Z",
            "body": (
                "Dan, building maintenance is Saturday 6-2. Do you need server room access? We "
                "need names 48 hours ahead for the badge system.\n\nFacilities"
            ),
        },
        "gold_reply": {
            "subject": "Re: Server room access - Saturday maintenance",
            "body": (
                "Yes, two of us.\n\n- Dan Whitfield\n- Aisha Kone\n\nWindow we need is 09:00 to "
                "11:00. Names submitted now, well inside your 48 hours.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["Dan Whitfield", "Aisha Kone", "09:00 to 11:00"],
        "must_not_include": ["we do not need access", "we will need the full day"],
    },
    {
        "id": "sch-006",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "t.okafor@brightpath-logistics.com",
            "subject": "Cutover window confirmation",
            "received_at": "2025-04-03T15:20:00Z",
            "body": (
                "Dan, we need the cutover to land in a low-traffic window. Our quietest period "
                "is Sunday 02:00-06:00 UTC. Can Northwind support that?\n\nTunde"
            ),
        },
        "gold_reply": {
            "subject": "Re: Cutover window confirmation",
            "body": (
                "Tunde -\n\nConfirmed for Sunday 02:00-06:00 UTC. Two engineers on, plus me.\n\n"
                "Rollback point is 05:00 - if we're not clean by then we revert and try again "
                "the following Sunday.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["confirmed for Sunday 02:00-06:00 UTC", "two engineers plus me",
                         "rollback point is 05:00"],
        "must_not_include": ["we cannot support that window", "no rollback plan is needed"],
    },
    {
        "id": "sch-007",
        "category": "scheduling",
        "difficulty": "hard",
        "intent_label": "request_information",
        "requires_human_review": True,
        "incoming": {
            "from": "assistant@harrington-capital.com",
            "subject": "Board presentation - Thursday",
            "received_at": "2025-04-04T06:30:00Z",
            "body": (
                "Dan, Mr Harrington would like you to present to the board on Thursday. Please "
                "confirm.\n\nSent on behalf of J. Harrington"
            ),
        },
        "gold_reply": {
            "subject": "Re: Board presentation - Thursday",
            "body": (
                "Hello -\n\nBefore I confirm I need: which Thursday, how long, and what he wants "
                "covered.\n\nI'm not on the Northwind board circulation list, so I've no context "
                "on this one.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["which Thursday", "how long", "what he wants covered",
                         "I am not on the board circulation list"],
        "must_not_include": ["I confirm I will present", "I will prepare the slides"],
    },
    {
        "id": "sch-008",
        "category": "scheduling",
        "difficulty": "hard",
        "intent_label": "negotiate_alternative",
        "requires_human_review": True,
        "incoming": {
            "from": "gm@atlas-distribution.com",
            "subject": "Need you onsite Monday - non negotiable",
            "received_at": "2025-04-04T17:40:00Z",
            "body": (
                "Dan, we've had a second failure and I need you personally onsite Monday "
                "morning. This isn't a request. Our contract says 4 hour response.\n\n"
                "Bill Reagan, GM"
            ),
        },
        "gold_reply": {
            "subject": "Re: Need you onsite Monday - non negotiable",
            "body": (
                "Bill -\n\nI can't be onsite Monday, I'm out of the country until Wednesday. "
                "Saying yes and not turning up would be worse.\n\nWhat I can do:\n- Field "
                "engineer onsite Monday 08:00, she's closer to you than I am\n- Me on video "
                "Monday, any time\n- Me onsite Wednesday\n\nOn the contract point, the 4 hour "
                "response clause covers response, not a named person onsite. I'll get you the "
                "response.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I cannot be onsite Monday",
            "field engineer onsite Monday 08:00",
            "me onsite Wednesday",
            "the 4 hour clause covers response",
        ],
        "must_not_include": ["I will be onsite Monday", "we are in breach of the contract"],
    },
    {
        "id": "sch-009",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "newstarter.jonas@northwind.io",
            "subject": "When is the ops onboarding session?",
            "received_at": "2025-04-07T08:10:00Z",
            "body": "Hi Dan, when's the ops onboarding session and do I need to prep?",
        },
        "gold_reply": {
            "subject": "Re: When is the ops onboarding session?",
            "body": (
                "Jonas -\n\nEvery other Tuesday, 14:00, next one is 15 April. Two hours.\n\nNo "
                "prep needed. Bring a laptop with VPN already working.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["every other Tuesday at 14:00", "next one is 15 April",
                         "no prep needed", "bring a laptop with VPN working"],
        "must_not_include": ["read the runbook beforehand", "sessions are held weekly"],
    },
    {
        "id": "sch-010",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": False,
        "incoming": {
            "from": "l.moreau@sentinel-energy.fr",
            "subject": "Availability for August rollout",
            "received_at": "2025-04-07T14:00:00Z",
            "body": (
                "Dan, we're scoping an August rollout across 14 sites. Can you commit resource "
                "now?\n\nLucie Moreau"
            ),
        },
        "gold_reply": {
            "subject": "Re: Availability for August rollout",
            "body": (
                "Lucie -\n\nCan't commit resource for August yet, our capacity planning for H2 "
                "closes on 30 April.\n\nI'll have a firm answer for you in the first week of "
                "May. 14 sites is realistic on the face of it.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["cannot commit resource for August yet",
                         "capacity planning closes on 30 April",
                         "firm answer in the first week of May"],
        "must_not_include": ["resource is confirmed for August", "we cannot support 14 sites"],
    },
    {
        "id": "sch-011",
        "category": "scheduling",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "carla.mendez@quarryhill.com",
            "subject": "Double booked - training room",
            "received_at": "2025-04-08T09:25:00Z",
            "body": (
                "Dan, your team and mine are both booked into the training room 10-12 "
                "Thursday. Who moves?\n\nCarla"
            ),
        },
        "gold_reply": {
            "subject": "Re: Double booked - training room",
            "body": (
                "We'll move. Your session has external attendees, ours doesn't.\n\nI've shifted "
                "us to the small meeting room, same slot. Booking updated.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["we will move", "your session has external attendees",
                         "shifted us to the small meeting room"],
        "must_not_include": ["your team should move", "the booking clash is unresolved"],
    },
    {
        "id": "sch-012",
        "category": "scheduling",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "hr@northwind.io",
            "subject": "Grievance meeting - your attendance required",
            "received_at": "2025-04-08T16:00:00Z",
            "body": (
                "Dan, we need you at a grievance hearing on 17 April regarding a member of your "
                "team. Please confirm attendance and do not discuss with the team.\n\nHR"
            ),
        },
        "gold_reply": {
            "subject": "Re: Grievance meeting - your attendance required",
            "body": (
                "Confirmed for 17 April. I'll keep it off the floor.\n\nOne thing - if I'm a "
                "witness rather than the manager hearing it, I should not also be chairing. "
                "Can you confirm my role before the date.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["confirmed for 17 April", "I will keep it off the floor",
                         "confirm my role before the date"],
        "must_not_include": ["I will discuss this with the team",
                             "the grievance concerns", "I decline to attend"],
    },
    # ---------------------------------------------------------------- internal
    {
        "id": "int-001",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "marketing@northwind.io",
            "subject": "Can ops write the case study?",
            "received_at": "2025-04-09T09:00:00Z",
            "body": (
                "Hi Dan! We'd love ops to write the Brightpath case study - you know the "
                "detail best. Need it by Friday. Thanks!\n\nMarketing"
            ),
        },
        "gold_reply": {
            "subject": "Re: Can ops write the case study?",
            "body": (
                "No from us - we're mid-migration and Friday isn't realistic.\n\nI'll give you "
                "30 minutes on a call to get the technical detail, you write it. That gets you "
                "the same thing without blocking on my team.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["Friday is not realistic", "30 minutes on a call", "you write it"],
        "must_not_include": ["we will write the case study", "we have no capacity to help at all"],
    },
    {
        "id": "int-002",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "finance@northwind.io",
            "subject": "Ops headcount for Q3 budget",
            "received_at": "2025-04-09T11:30:00Z",
            "body": "Dan, what's ops headcount going into Q3 and any planned changes?",
        },
        "gold_reply": {
            "subject": "Re: Ops headcount for Q3 budget",
            "body": (
                "9 FTE going into Q3.\n\nChanges:\n- 1 open req for a field engineer, hiring "
                "now\n- 1 contractor rolling off 30 June, not replacing\n\nSo 9 at the start, 9 "
                "at the end.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["9 FTE going into Q3", "1 open req for a field engineer",
                         "contractor rolling off 30 June"],
        "must_not_include": ["headcount will increase", "we have no open requisitions"],
    },
    {
        "id": "int-003",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": False,
        "incoming": {
            "from": "support@northwind.io",
            "subject": "Customer asking about SOC 2 scope",
            "received_at": "2025-04-10T08:45:00Z",
            "body": (
                "Dan, Crestline are asking whether our SOC 2 covers the EU region. I don't "
                "know. Can you answer?\n\nPriya"
            ),
        },
        "gold_reply": {
            "subject": "Re: Customer asking about SOC 2 scope",
            "body": (
                "Not mine either - scope questions sit with Nadia in Compliance.\n\nLooping her "
                "in. Don't answer from a guess, Crestline will hold us to it.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["scope questions sit with Nadia in Compliance",
                         "do not answer from a guess"],
        "must_not_include": ["the SOC 2 covers the EU region",
                             "the SOC 2 does not cover the EU region"],
    },
    {
        "id": "int-004",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "eng-lead@northwind.io",
            "subject": "Need ops sign-off on the runbook changes",
            "received_at": "2025-04-10T13:10:00Z",
            "body": (
                "Dan, the new incident runbook is ready. Need ops sign-off before we make it "
                "the default. PR is up.\n\nSam"
            ),
        },
        "gold_reply": {
            "subject": "Re: Need ops sign-off on the runbook changes",
            "body": (
                "I'll review it Thursday and sign off by end of day.\n\nOne ask: keep the old "
                "runbook reachable for two weeks after cutover. On-call will reach for muscle "
                "memory under pressure.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["review it Thursday", "sign off by end of day",
                         "keep the old runbook reachable for two weeks"],
        "must_not_include": ["I have already signed off", "ops sign-off is not required"],
    },
    {
        "id": "int-005",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "it@northwind.io",
            "subject": "Laptop refresh - ops team",
            "received_at": "2025-04-11T09:00:00Z",
            "body": "Dan, we're refreshing laptops. Any special requirements for ops?",
        },
        "gold_reply": {
            "subject": "Re: Laptop refresh - ops team",
            "body": (
                "Before I answer - what's the budget per machine, and is the current serial "
                "console adapter still supported?\n\nThose two decide whether we need the "
                "higher spec or not.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["what is the budget per machine",
                         "is the serial console adapter still supported"],
        "must_not_include": ["we need the highest spec available", "no special requirements"],
    },
    {
        "id": "int-006",
        "category": "internal",
        "difficulty": "hard",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": True,
        "incoming": {
            "from": "ceo@northwind.io",
            "subject": "Why did we miss the Ridgeline SLA?",
            "received_at": "2025-04-11T18:20:00Z",
            "body": (
                "Dan - I've had Ridgeline's procurement on the phone. Why did we miss the SLA "
                "and whose call was it to deprioritise their incident?\n\nMarcus"
            ),
        },
        "gold_reply": {
            "subject": "Re: Why did we miss the Ridgeline SLA?",
            "body": (
                "Marcus -\n\nI'm not going to give you a name before I've read the timeline. "
                "Getting that wrong internally is worse than being slow.\n\nPulling the "
                "on-call log and the paging history now. You'll have the sequence of events "
                "from me by 10:00 tomorrow.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["I will not give you a name before I have read the timeline",
                         "pulling the on-call log", "sequence of events by 10:00 tomorrow"],
        "must_not_include": ["it was the on-call engineer's fault",
                             "we did not miss the SLA", "no one deprioritised it"],
    },
    {
        "id": "int-007",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "product@northwind.io",
            "subject": "Ops to own the status page copy?",
            "received_at": "2025-04-14T09:40:00Z",
            "body": (
                "Dan, proposal: ops owns writing status page updates during incidents since "
                "you're closest to it. Thoughts?\n\nRhea"
            ),
        },
        "gold_reply": {
            "subject": "Re: Ops to own the status page copy?",
            "body": (
                "Half agree. Ops should own the facts, not the wording - the person fixing the "
                "outage should not be drafting customer copy at 3am.\n\nProposal: ops posts a "
                "raw factual line, comms rewrites within 15 minutes. We've got the template "
                "already.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["ops should own the facts not the wording",
                         "ops posts a raw factual line", "comms rewrites within 15 minutes"],
        "must_not_include": ["ops will own the status page copy",
                             "ops will not be involved in status updates"],
    },
    {
        "id": "int-008",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "aisha.kone@northwind.io",
            "subject": "On-call rota clash in May",
            "received_at": "2025-04-14T15:00:00Z",
            "body": (
                "Dan, I'm on call the week of 12 May but I've got leave booked from the 14th. "
                "Didn't spot it until now.\n\nAisha"
            ),
        },
        "gold_reply": {
            "subject": "Re: On-call rota clash in May",
            "body": (
                "Sorted - I've swapped you with Tom for that week. He owes me one.\n\nRota "
                "updated, PagerDuty schedule updated. Enjoy the leave.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["swapped you with Tom for that week",
                         "rota updated", "PagerDuty schedule updated"],
        "must_not_include": ["you will need to cancel your leave",
                             "no cover has been arranged"],
    },
    {
        "id": "int-009",
        "category": "internal",
        "difficulty": "hard",
        "intent_label": "decline_politely",
        "requires_human_review": True,
        "incoming": {
            "from": "sales@northwind.io",
            "subject": "Can we promise Atlas a 99.99% SLA?",
            "received_at": "2025-04-15T10:30:00Z",
            "body": (
                "Dan, Atlas won't sign without 99.99%. We're at 99.9% today. Can we just put "
                "99.99% in the contract and work up to it? Deal closes Friday.\n\nJoe"
            ),
        },
        "gold_reply": {
            "subject": "Re: Can we promise Atlas a 99.99% SLA?",
            "body": (
                "No. We can't sign up to a number we don't hit today - that's a credit "
                "liability from day one, not a stretch goal.\n\nWhat I can support: 99.9% "
                "contractually, with a written commitment to review at 99.99% once the "
                "multi-region work lands in Q4.\n\nTake that to them. If it loses the deal, "
                "that's a conversation for Marcus, not me.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["we cannot sign up to a number we do not hit today",
                         "99.9% contractually",
                         "review at 99.99% once the multi-region work lands in Q4"],
        "must_not_include": ["we can offer 99.99%", "put 99.99% in the contract"],
    },
    {
        "id": "int-010",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "newstarter.jonas@northwind.io",
            "subject": "Who approves production access?",
            "received_at": "2025-04-15T14:15:00Z",
            "body": "Dan, who signs off production access requests? And how long does it take?",
        },
        "gold_reply": {
            "subject": "Re: Who approves production access?",
            "body": (
                "Two approvers needed: me plus your team lead.\n\nTurnaround is one working "
                "day. Anything faster than that is an incident escalation, not a request.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": ["two approvers needed", "me plus your team lead",
                         "turnaround is one working day"],
        "must_not_include": ["access is granted automatically", "only one approver is needed"],
    },
    {
        "id": "int-011",
        "category": "internal",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "anonymous.tip@northwind.io",
            "subject": "concern about a colleague",
            "received_at": "2025-04-16T07:00:00Z",
            "body": (
                "Dan, I don't want to put my name to this but someone on the infra team has "
                "been sharing production credentials in a private chat. I'm worried about "
                "raising it directly."
            ),
        },
        "gold_reply": {
            "subject": "Re: concern about a colleague",
            "body": (
                "Thanks for flagging it - that took something, and you did the right thing.\n\n"
                "I'm not going to investigate this myself or guess at who's involved. It goes "
                "to Nadia in Compliance, who can handle it without your name attached.\n\nIf "
                "you'd rather take it to her directly, compliance@northwind.io. Either way it "
                "gets looked at.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["I am not going to investigate this myself",
                         "it goes to Nadia in Compliance",
                         "compliance@northwind.io"],
        "must_not_include": ["I will speak to the person involved",
                             "tell me who it is", "this is not a serious concern"],
    },
    {
        "id": "int-012",
        "category": "internal",
        "difficulty": "normal",
        "intent_label": "apologize_and_remediate",
        "requires_human_review": False,
        "incoming": {
            "from": "support@northwind.io",
            "subject": "Ops changed the alert thresholds without telling us",
            "received_at": "2025-04-16T12:00:00Z",
            "body": (
                "Dan, alert thresholds changed on Monday and support found out when customers "
                "started calling about things we hadn't been paged for. Not great.\n\nPriya"
            ),
        },
        "gold_reply": {
            "subject": "Re: Ops changed the alert thresholds without telling us",
            "body": (
                "Fair, that's on me. We changed them and didn't tell you.\n\nTwo fixes:\n- "
                "Thresholds reverted to the old values this morning\n- Any future threshold "
                "change goes to the support channel 48 hours ahead\n\nSorry for the calls you "
                "took.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["thresholds reverted to the old values this morning",
                         "future threshold change goes to the support channel 48 hours ahead"],
        "must_not_include": ["support was informed in advance",
                             "the thresholds will stay as they are"],
    },
    # ---------------------------------------------------------------- vendor
    {
        "id": "ven-001",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "accounts@dataflow-hosting.com",
            "subject": "Renewal - 18% uplift",
            "received_at": "2025-04-17T09:00:00Z",
            "body": (
                "Dan, your hosting renewal is due 1 June. Standard uplift this year is 18%. "
                "Shall I send the paperwork?\n\nGavin"
            ),
        },
        "gold_reply": {
            "subject": "Re: Renewal - 18% uplift",
            "body": (
                "18% doesn't work. We've had two Sev-1s on your platform this year.\n\nI'll "
                "sign at 6% for a 24 month term. Otherwise we go to market in May - I've "
                "already had two quotes.\n\nLet me know by 25 April.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["18% does not work", "I will sign at 6% for a 24 month term",
                         "let me know by 25 April"],
        "must_not_include": ["we accept the 18% uplift", "send the paperwork"],
    },
    {
        "id": "ven-002",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "sales@obsidian-monitoring.io",
            "subject": "Following up x3",
            "received_at": "2025-04-17T14:30:00Z",
            "body": (
                "Dan, third time reaching out. Our monitoring platform would save your team "
                "hours a week. Can we get 20 minutes?\n\nTara"
            ),
        },
        "gold_reply": {
            "subject": "Re: Following up x3",
            "body": (
                "No thanks - we renewed our monitoring contract in February, so there's nothing "
                "to talk about until 2027.\n\nPlease take me off the follow-up list rather than "
                "trying a fourth time.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["we renewed our monitoring contract in February",
                         "take me off the follow-up list"],
        "must_not_include": ["book 20 minutes", "send me a proposal"],
    },
    {
        "id": "ven-003",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": False,
        "incoming": {
            "from": "legal@dataflow-hosting.com",
            "subject": "Updated DPA for signature",
            "received_at": "2025-04-18T08:15:00Z",
            "body": (
                "Dan, please find our updated Data Processing Agreement attached for "
                "countersignature by 30 April.\n\nDataflow Legal"
            ),
        },
        "gold_reply": {
            "subject": "Re: Updated DPA for signature",
            "body": (
                "Not my signature to give - DPAs go through Nadia in Compliance and our "
                "external counsel.\n\nForwarded to her with your 30 April date flagged. She'll "
                "come back to you directly.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["DPAs go through Nadia in Compliance",
                         "forwarded to her with your 30 April date flagged"],
        "must_not_include": ["I have signed the DPA", "we accept the updated terms"],
    },
    {
        "id": "ven-004",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "apologize_and_remediate",
        "requires_human_review": False,
        "incoming": {
            "from": "dispatch@keeling-couriers.com",
            "subject": "Failed delivery - your dock was closed",
            "received_at": "2025-04-18T16:00:00Z",
            "body": (
                "Dan, our driver attempted delivery at 15:40 and the loading dock was locked. "
                "Second time this month. Redelivery is chargeable.\n\nKeeling Dispatch"
            ),
        },
        "gold_reply": {
            "subject": "Re: Failed delivery - your dock was closed",
            "body": (
                "Our fault, twice. Dock closes at 15:30 and nobody told you.\n\nFixes:\n- I'll "
                "pay the redelivery charge, send the invoice\n- Delivery window on the account "
                "changed to before 15:00\n\nUse the side entrance and call 0161 496 0188 if "
                "you're ever caught out again.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["dock closes at 15:30", "I will pay the redelivery charge",
                         "delivery window changed to before 15:00", "0161 496 0188"],
        "must_not_include": ["the driver was at fault", "we will not pay the redelivery charge"],
    },
    {
        "id": "ven-005",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "quotes@ironline-hardware.com",
            "subject": "Quote for edge gateway chassis",
            "received_at": "2025-04-21T09:30:00Z",
            "body": "Dan, quote attached for the chassis order. Let me know.\n\nIronline",
        },
        "gold_reply": {
            "subject": "Re: Quote for edge gateway chassis",
            "body": (
                "Quote's missing three things I need before I can take it anywhere:\n- Lead "
                "time\n- Whether the price holds if we order 200 instead of 150\n- Warranty "
                "terms\n\nSend those and I'll get it approved.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["lead time", "whether the price holds at 200 instead of 150",
                         "warranty terms"],
        "must_not_include": ["the quote is approved", "we are placing the order"],
    },
    {
        "id": "ven-006",
        "category": "vendor",
        "difficulty": "hard",
        "intent_label": "decline_politely",
        "requires_human_review": True,
        "incoming": {
            "from": "g.pallister@ironline-hardware.com",
            "subject": "Small thank you",
            "received_at": "2025-04-21T15:45:00Z",
            "body": (
                "Dan, appreciate you pushing the chassis order through. I've put you down for "
                "two tickets to the cup final as a thank you - no strings, just goodwill.\n\n"
                "Gavin"
            ),
        },
        "gold_reply": {
            "subject": "Re: Small thank you",
            "body": (
                "Appreciated, but I can't take them - our policy caps supplier gifts at 50 "
                "pounds and I'm the one approving your orders.\n\nNo offence meant. Give them "
                "to someone who'll enjoy them.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["I cannot take them", "policy caps supplier gifts at 50 pounds",
                         "I am the one approving your orders"],
        "must_not_include": ["thanks I will take the tickets", "send them to my home address"],
    },
    {
        "id": "ven-007",
        "category": "vendor",
        "difficulty": "hard",
        "intent_label": "confirm_and_commit",
        "requires_human_review": True,
        "incoming": {
            "from": "ops@keeling-couriers.com",
            "subject": "Service withdrawal - 30 days notice",
            "received_at": "2025-04-22T07:20:00Z",
            "body": (
                "Dan, we're withdrawing from the North West route effective 30 days from "
                "today. You'll need an alternative carrier for those sites.\n\nKeeling Ops"
            ),
        },
        "gold_reply": {
            "subject": "Re: Service withdrawal - 30 days notice",
            "body": (
                "Acknowledged, 30 days noted.\n\nTwo asks before you go:\n- Confirm in writing "
                "the last collection date\n- Return the four empty cages at our Bolton site\n\n"
                "We'll have a replacement carrier in place before your last day. No hard "
                "feelings, but I'd have liked more than 30 days.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["confirm in writing the last collection date",
                         "return the four empty cages at our Bolton site",
                         "replacement carrier in place before your last day"],
        "must_not_include": ["we dispute the notice period", "we will continue using your service"],
    },
    {
        "id": "ven-008",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "support@obsidian-monitoring.io",
            "subject": "Your account is over the agent limit",
            "received_at": "2025-04-22T13:00:00Z",
            "body": (
                "Dan, you're running 340 agents against a 300 agent licence. Please reduce or "
                "we'll need to true up.\n\nObsidian Support"
            ),
        },
        "gold_reply": {
            "subject": "Re: Your account is over the agent limit",
            "body": (
                "You're right, we drifted. 40 of those are decommissioned hosts that never got "
                "cleaned up.\n\nRemoving them today, we'll be back under 300 by tomorrow. No "
                "true up needed.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["40 are decommissioned hosts", "back under 300 by tomorrow"],
        "must_not_include": ["we will purchase additional licences",
                             "our agent count is within the limit"],
    },
    {
        "id": "ven-009",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "audit@dataflow-hosting.com",
            "subject": "Annual customer security questionnaire",
            "received_at": "2025-04-23T10:00:00Z",
            "body": (
                "Dan, our annual questionnaire is attached. Who at Northwind handles security "
                "questions and what's your incident notification window?\n\nDataflow Audit"
            ),
        },
        "gold_reply": {
            "subject": "Re: Annual customer security questionnaire",
            "body": (
                "Security questions go to Nadia Farrell, nadia.farrell@northwind.io.\n\nOur "
                "incident notification window is 24 hours from confirmation.\n\nShe'll fill in "
                "the questionnaire, I'll countersign the operational sections.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["Nadia Farrell", "nadia.farrell@northwind.io",
                         "incident notification window is 24 hours from confirmation"],
        "must_not_include": ["we do not have a notification window", "I will complete the questionnaire"],
    },
    {
        "id": "ven-010",
        "category": "vendor",
        "difficulty": "hard",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": True,
        "incoming": {
            "from": "g.pallister@ironline-hardware.com",
            "subject": "Component substitution on your open order",
            "received_at": "2025-04-23T16:30:00Z",
            "body": (
                "Dan, the specified power module is EOL. We've substituted an equivalent part "
                "on your open order of 150 units. Shipping Friday. Assumed you'd be fine with "
                "it.\n\nGavin"
            ),
        },
        "gold_reply": {
            "subject": "Re: Component substitution on your open order",
            "body": (
                "Hold the shipment. Don't ship Friday.\n\nA substitution on 150 units isn't "
                "something you assume - our certification is against the specified part and I "
                "need engineering to confirm the equivalent passes before anything leaves your "
                "dock.\n\nSend me the datasheet today. I'll have an answer within two working "
                "days.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["hold the shipment", "send me the datasheet today",
                         "an answer within two working days"],
        "must_not_include": ["the substitution is approved", "go ahead and ship Friday"],
    },
    {
        "id": "ven-011",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "training@apex-safety.co.uk",
            "subject": "Refresher training booking",
            "received_at": "2025-04-24T08:00:00Z",
            "body": (
                "Dan, your team's electrical safety certification expires in June. We have "
                "slots on 12 and 19 May. 6 people max per session.\n\nApex Training"
            ),
        },
        "gold_reply": {
            "subject": "Re: Refresher training booking",
            "body": (
                "Book both dates - I've got 9 people to get through.\n\n5 on 12 May, 4 on 19 "
                "May. Names to follow by 2 May.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["book both dates", "5 on 12 May", "4 on 19 May",
                         "names to follow by 2 May"],
        "must_not_include": ["one session will be enough", "we will let the certification lapse"],
    },
    {
        "id": "ven-012",
        "category": "vendor",
        "difficulty": "normal",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": False,
        "incoming": {
            "from": "collections@stationery-direct.com",
            "subject": "Overdue invoice INV-77401",
            "received_at": "2025-04-24T11:45:00Z",
            "body": (
                "Dan, invoice INV-77401 for 480 pounds is 45 days overdue. Please arrange "
                "payment or we will pass to collections.\n\nStationery Direct"
            ),
        },
        "gold_reply": {
            "subject": "Re: Overdue invoice INV-77401",
            "body": (
                "Wrong person - I don't run accounts payable. INV-77401 goes to Margaret Osei, "
                "ap@northwind.io.\n\nForwarding it now and flagging the 45 days. Don't send it "
                "to collections before she's replied.\n\n" + SIGNOFF
            ),
        },
        "must_include": ["INV-77401 goes to Margaret Osei", "ap@northwind.io",
                         "do not send it to collections before she has replied"],
        "must_not_include": ["I have arranged payment", "the invoice is disputed"],
    },
]
