"""Inbox of Margaret Osei, Business Manager at Northwind Systems.

Categories: billing, sales, recruiting. At a 40-person company one person owns invoicing,
quoting and hiring administration, which is why these three sit together.

The most formal of the three personas: no contractions, explicit figures and reference
numbers, full signature block every time. Records here carry the densest numeric
constraints in the dataset, which is deliberate — they are the ones that catch a fluent
reply quoting a plausible but wrong number.
"""

SIGNOFF = "Kind regards,\nMargaret Osei\nBusiness Manager, Northwind Systems"

RECORDS = [
    # ---------------------------------------------------------------- billing
    {
        "id": "bil-001",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "ap@brightpath-logistics.com",
            "subject": "Query on invoice INV-20412",
            "received_at": "2025-05-02T09:00:00Z",
            "body": (
                "Hello,\n\nInvoice INV-20412 shows a line for 'overage - 1.2M records' at 840 "
                "pounds. Our records show we stayed within plan. Can you explain the "
                "charge?\n\nAccounts Payable, Brightpath"
            ),
        },
        "gold_reply": {
            "subject": "Re: Query on invoice INV-20412",
            "body": (
                "Hello,\n\nThank you for raising this. I have reviewed invoice INV-20412.\n\n"
                "The overage line of 840 pounds relates to the period 1 to 31 March, during "
                "which your account processed 4.2 million records against a plan allowance of "
                "3.0 million. The 1.2 million excess is charged at 0.07 pounds per thousand "
                "records.\n\nYour plan allowance resets on the first of each month, so a mid-"
                "month peak can exceed the allowance even where the quarterly average does "
                "not. I have attached the daily breakdown so that you may verify this.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "INV-20412",
            "4.2 million records against an allowance of 3.0 million",
            "0.07 pounds per thousand records",
            "the allowance resets on the first of each month",
        ],
        "must_not_include": ["the charge was applied in error", "I have credited the 840 pounds"],
    },
    {
        "id": "bil-002",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "apologize_and_remediate",
        "requires_human_review": False,
        "incoming": {
            "from": "finance@vertexmfg.io",
            "subject": "We have been double charged",
            "received_at": "2025-05-02T14:30:00Z",
            "body": (
                "Margaret, we have two identical charges of 2,400 pounds on 1 May. Please "
                "refund one of them.\n\nVertex Finance"
            ),
        },
        "gold_reply": {
            "subject": "Re: We have been double charged",
            "body": (
                "Hello,\n\nYou are correct and I apologise. Two charges of 2,400 pounds were "
                "raised on 1 May due to a retry on our payment processor.\n\nI have refunded "
                "the duplicate charge today. Funds typically return to the originating card "
                "within 5 to 10 working days depending on your bank. The refund reference is "
                "REF-88120.\n\nI have also credited 50 pounds against your next invoice in "
                "recognition of the inconvenience.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "two charges of 2,400 pounds were raised on 1 May",
            "I have refunded the duplicate charge today",
            "5 to 10 working days",
            "REF-88120",
        ],
        "must_not_include": ["only one charge was raised", "the refund will take 30 days"],
    },
    {
        "id": "bil-003",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "cfo@harlow-foods.co.uk",
            "subject": "Request to move to annual billing mid-term",
            "received_at": "2025-05-05T08:20:00Z",
            "body": (
                "Margaret, we would like to switch from monthly to annual billing now and "
                "receive the annual discount backdated to January.\n\nHarlow Finance"
            ),
        },
        "gold_reply": {
            "subject": "Re: Request to move to annual billing mid-term",
            "body": (
                "Hello,\n\nThank you for the request. I am able to move you to annual billing "
                "from 1 June, which attracts the standard 10 per cent annual discount.\n\nI am "
                "not able to backdate the discount to January. The discount is consideration "
                "for payment in advance, and the January to May period was invoiced monthly "
                "and settled in arrears.\n\nIf you would like to proceed on that basis, I will "
                "issue the revised schedule for your approval before anything is charged.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "annual billing from 1 June",
            "10 per cent annual discount",
            "I am not able to backdate the discount to January",
            "revised schedule for your approval",
        ],
        "must_not_include": ["the discount has been backdated", "I have applied a January credit"],
    },
    {
        "id": "bil-004",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "procurement@crestline-bank.com",
            "subject": "Purchase order number required on invoices",
            "received_at": "2025-05-05T11:00:00Z",
            "body": (
                "Margaret, our AP system rejects invoices without a PO reference. Going "
                "forward please quote PO-4471-CB on every invoice.\n\nCrestline Procurement"
            ),
        },
        "gold_reply": {
            "subject": "Re: Purchase order number required on invoices",
            "body": (
                "Hello,\n\nNoted with thanks. I have added PO-4471-CB to your billing profile, "
                "and it will appear on every invoice issued from today.\n\nYour most recent "
                "invoice, INV-20455, was issued before this change. I will reissue it with the "
                "purchase order reference and cancel the original, so that your accounts "
                "payable system accepts it.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "PO-4471-CB added to your billing profile",
            "INV-20455",
            "I will reissue it with the purchase order reference",
        ],
        "must_not_include": ["we cannot add purchase order references",
                             "no further action is required from us"],
    },
    {
        "id": "bil-005",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "accounts@northstar-retail.se",
            "subject": "Payment sent",
            "received_at": "2025-05-06T09:45:00Z",
            "body": "Hi, we sent the payment last week. Please confirm receipt.\n\nNorthstar",
        },
        "gold_reply": {
            "subject": "Re: Payment sent",
            "body": (
                "Hello,\n\nThank you for letting me know. I am unable to locate a payment "
                "against your account in the last seven days.\n\nIn order to trace it, please "
                "send me the payment date, the amount, and the remittance reference used. If "
                "the payment was made by bank transfer, the last four digits of the "
                "originating account would also help.\n\nOnce I have those details I will "
                "confirm receipt or investigate further the same day.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "unable to locate a payment in the last seven days",
            "the payment date",
            "the remittance reference used",
        ],
        "must_not_include": ["I confirm receipt of your payment", "your account is now settled"],
    },
    {
        "id": "bil-006",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "ops@quarryhill.com",
            "subject": "Waive the late fee?",
            "received_at": "2025-05-06T15:10:00Z",
            "body": (
                "Margaret, we were charged a 120 pound late fee on INV-20388. It was late "
                "because our approver was on leave. Any chance of waiving it?\n\nQuarryhill"
            ),
        },
        "gold_reply": {
            "subject": "Re: Waive the late fee?",
            "body": (
                "Hello,\n\nThank you for explaining the circumstances. I have reviewed the "
                "account and I am not able to waive the 120 pound fee on INV-20388, as this is "
                "the third late payment in six months and the fee has been waived once "
                "already.\n\nWhat I can offer is a change to your payment terms: moving you to "
                "direct debit would remove the dependency on a single approver and prevent a "
                "recurrence. There is no charge for making that change.\n\nPlease let me know "
                "whether you would like me to arrange it.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to waive the 120 pound fee",
            "INV-20388",
            "the third late payment in six months",
            "moving you to direct debit",
        ],
        "must_not_include": ["the late fee has been waived", "I have credited 120 pounds"],
    },
    {
        "id": "bil-007",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "ap@sentinel-energy.fr",
            "subject": "VAT treatment incorrect on our invoices",
            "received_at": "2025-05-07T08:00:00Z",
            "body": (
                "Margaret, you are charging UK VAT on our invoices. We are a French registered "
                "business with a valid VAT number, FR40123456789. This should be reverse "
                "charge.\n\nSentinel Finance"
            ),
        },
        "gold_reply": {
            "subject": "Re: VAT treatment incorrect on our invoices",
            "body": (
                "Hello,\n\nThank you for providing the VAT number. You are correct: with a "
                "valid EU VAT registration the supply should be treated as reverse charge and "
                "UK VAT should not be applied.\n\nI have recorded FR40123456789 against your "
                "account and validated it. All invoices issued from today will apply the "
                "reverse charge treatment.\n\nFor the three invoices already issued this year, "
                "I will raise credit notes and reissue them correctly. You should receive "
                "these within five working days.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "FR40123456789 recorded against your account",
            "reverse charge treatment from today",
            "credit notes for the three invoices already issued",
            "within five working days",
        ],
        "must_not_include": ["UK VAT is correctly applied", "no correction is required"],
    },
    {
        "id": "bil-008",
        "category": "billing",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "k.bauer@wildeneck-ag.de",
            "subject": "Withholding payment pending service credits",
            "received_at": "2025-05-07T13:30:00Z",
            "body": (
                "Margaret, we are withholding the 18,000 euro payment due 15 May until the "
                "service credits from the March outages are agreed. Please confirm you accept "
                "this.\n\nKlaus Bauer"
            ),
        },
        "gold_reply": {
            "subject": "Re: Withholding payment pending service credits",
            "body": (
                "Hello,\n\nThank you for setting out your position clearly. I am not in a "
                "position to accept or reject a withholding of the 18,000 euro payment, as "
                "that determination sits with our commercial team under the terms of the "
                "master agreement.\n\nI have referred your message to Karim Aslan, your account "
                "director, today and asked him to respond before the 15 May due date.\n\nSo "
                "that the credit calculation is not the bottleneck, I have separately asked "
                "our operations team for the March availability figures.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not in a position to accept or reject the withholding",
            "referred to Karim Aslan your account director",
            "respond before the 15 May due date",
        ],
        "must_not_include": [
            "we accept the withholding of payment",
            "the service credits are agreed",
            "your account will be suspended",
        ],
    },
    {
        "id": "bil-009",
        "category": "billing",
        "difficulty": "hard",
        "intent_label": "request_information",
        "requires_human_review": True,
        "incoming": {
            "from": "newfinance@atlascargo.fr",
            "subject": "Change of bank details for future payments",
            "received_at": "2025-05-08T07:15:00Z",
            "body": (
                "Hello Margaret, we have changed banks. Please update your records so that our "
                "refunds go to the new account: IBAN FR76 3000 4000 0300 0012 3456 789. Kindly "
                "action today as we have a refund pending.\n\nAtlas Cargo Finance"
            ),
        },
        "gold_reply": {
            "subject": "Re: Change of bank details for future payments",
            "body": (
                "Hello,\n\nThank you for notifying me. I am not able to change payment details "
                "on the basis of an email alone, as bank detail changes are a common route for "
                "payment fraud and this protects both of us.\n\nOur process requires two "
                "steps: a signed change of bank details form on your company letterhead, and a "
                "verbal confirmation from a known contact on the telephone number already held "
                "on your account.\n\nI will send the form today. Once both steps are complete I "
                "will update the record and release any pending refund.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to change payment details on the basis of an email alone",
            "a signed change of bank details form on company letterhead",
            "verbal confirmation on the telephone number already held",
        ],
        "must_not_include": [
            "I have updated your bank details",
            "the refund has been sent to the new account",
        ],
    },
    {
        "id": "bil-010",
        "category": "billing",
        "difficulty": "hard",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": True,
        "incoming": {
            "from": "t.okafor@brightpath-logistics.com",
            "subject": "Why has our renewal price gone up 32 per cent?",
            "received_at": "2025-05-08T16:00:00Z",
            "body": (
                "Margaret, the renewal quote is 32 per cent above last year. Nobody flagged "
                "this. We budgeted on a single digit increase. I need an explanation and I "
                "need it before our board meets on Monday.\n\nTunde Okafor"
            ),
        },
        "gold_reply": {
            "subject": "Re: Why has our renewal price gone up 32 per cent?",
            "body": (
                "Hello Tunde,\n\nThank you for raising this before Monday rather than after.\n\n"
                "I can see the 32 per cent increase on the quote. I am not yet able to tell you "
                "how much of it is list price movement and how much is a change in your "
                "committed volume, because the quote was generated by our sales system and I do "
                "not hold the underlying assumptions.\n\nI have requested the breakdown today "
                "and will send you a line by line comparison against last year by close of "
                "business Friday, which gives you the weekend before the board.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not yet able to tell you how much is list price movement",
            "I have requested the breakdown today",
            "line by line comparison by close of business Friday",
        ],
        "must_not_include": [
            "the increase is due to list price changes",
            "I have reduced the renewal price",
            "the quote is incorrect",
        ],
    },
    {
        "id": "bil-011",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "audit@marlowe-insurance.co.uk",
            "subject": "Copy invoices for financial year 2024",
            "received_at": "2025-05-09T09:30:00Z",
            "body": (
                "Margaret, our auditors require copies of all Northwind invoices for FY2024. "
                "Can you provide these?\n\nMarlowe Audit"
            ),
        },
        "gold_reply": {
            "subject": "Re: Copy invoices for financial year 2024",
            "body": (
                "Hello,\n\nCertainly. There are 12 invoices covering the period 1 April 2024 to "
                "31 March 2025, totalling 54,600 pounds excluding VAT.\n\nI have generated a "
                "single PDF pack and sent it to this address. Should your auditors require them "
                "individually, or in a machine readable format, I can provide a CSV of the same "
                "data on request.\n\nPlease note that invoice INV-20301 was credited in full "
                "and reissued as INV-20309; both documents are included for completeness.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "12 invoices covering 1 April 2024 to 31 March 2025",
            "54,600 pounds excluding VAT",
            "INV-20301 was credited in full and reissued as INV-20309",
        ],
        "must_not_include": ["we do not retain historical invoices",
                             "a fee applies for copy invoices"],
    },
    {
        "id": "bil-012",
        "category": "billing",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "cfo@junipertrade.com",
            "subject": "Request for payment plan",
            "received_at": "2025-05-09T14:20:00Z",
            "body": (
                "Margaret, cash flow is tight this quarter. Could we settle the 9,000 pound "
                "balance over three months rather than in one payment?\n\nJuniper Finance"
            ),
        },
        "gold_reply": {
            "subject": "Re: Request for payment plan",
            "body": (
                "Hello,\n\nThank you for contacting me in advance rather than allowing the "
                "invoice to fall overdue. That is appreciated and it makes this "
                "straightforward.\n\nI can agree to three monthly instalments of 3,000 pounds, "
                "due on 1 June, 1 July and 1 August. No interest or late fees will be applied "
                "provided the instalments are met.\n\nI will send a short written agreement for "
                "signature today. Your service will continue unaffected throughout.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "three monthly instalments of 3,000 pounds",
            "due on 1 June, 1 July and 1 August",
            "no interest or late fees provided the instalments are met",
        ],
        "must_not_include": ["we require payment in full immediately",
                             "your service will be suspended"],
    },
    # ---------------------------------------------------------------- sales
    {
        "id": "sal-001",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "it.director@pinehurst-labs.com",
            "subject": "Pricing for 250 seats",
            "received_at": "2025-05-12T08:45:00Z",
            "body": (
                "Hello, we are evaluating Relay for approximately 250 users. Could you send "
                "indicative pricing and tell us what is included?\n\nPinehurst Labs"
            ),
        },
        "gold_reply": {
            "subject": "Re: Pricing for 250 seats",
            "body": (
                "Hello,\n\nThank you for your interest in Relay.\n\nAt 250 seats you would fall "
                "into our Scale tier, which is 18 pounds per seat per month on an annual "
                "commitment, giving an indicative annual figure of 54,000 pounds.\n\nThat "
                "includes unlimited connectors, the full API, SFTP export, 400 day log "
                "retention and named technical support. Implementation is quoted separately "
                "and typically falls between 4,000 and 9,000 pounds depending on the number of "
                "source systems.\n\nI would be glad to arrange a scoping call if that would be "
                "useful.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "Scale tier at 18 pounds per seat per month",
            "indicative annual figure of 54,000 pounds",
            "implementation between 4,000 and 9,000 pounds",
        ],
        "must_not_include": ["implementation is included at no cost",
                             "pricing is fixed and non negotiable"],
    },
    {
        "id": "sal-002",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "procurement@fenwick-analytics.com",
            "subject": "Discount request - 35 per cent",
            "received_at": "2025-05-12T13:00:00Z",
            "body": (
                "Margaret, we have a competing quote materially below yours. We would need 35 "
                "per cent off list to proceed.\n\nFenwick Procurement"
            ),
        },
        "gold_reply": {
            "subject": "Re: Discount request - 35 per cent",
            "body": (
                "Hello,\n\nThank you for being direct about the position.\n\nI am not able to "
                "approve 35 per cent off list. Our maximum standard discount is 15 per cent, "
                "and anything beyond that requires a commercial justification that I do not "
                "currently have.\n\nThere are two routes that close more of the gap than a "
                "discount alone. A three year term attracts 22 per cent, and moving your "
                "renewal date to align with our financial year end in October would allow me "
                "to request a further concession.\n\nIf you can share the scope of the "
                "competing quote, I can tell you honestly whether we are comparing like with "
                "like.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to approve 35 per cent off list",
            "maximum standard discount is 15 per cent",
            "a three year term attracts 22 per cent",
        ],
        "must_not_include": ["35 per cent is approved", "we will match any competing quote"],
    },
    {
        "id": "sal-003",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "coo@caldera-systems.pt",
            "subject": "Proceeding with the Scale proposal",
            "received_at": "2025-05-13T09:10:00Z",
            "body": (
                "Margaret, the board approved. We would like to proceed with the Scale "
                "proposal, 120 seats, starting 1 July.\n\nCaldera Systems"
            ),
        },
        "gold_reply": {
            "subject": "Re: Proceeding with the Scale proposal",
            "body": (
                "Hello,\n\nThat is excellent news, and thank you for confirming.\n\nI will issue "
                "the order form for 120 Scale seats with a start date of 1 July today. It will "
                "come to you for electronic signature and requires no purchase order unless "
                "your process demands one.\n\nOn countersignature I will introduce you to our "
                "onboarding team, who will contact you within two working days to agree an "
                "implementation schedule ahead of 1 July.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "order form for 120 Scale seats",
            "start date of 1 July",
            "onboarding team will contact you within two working days",
        ],
        "must_not_include": ["we are unable to meet the 1 July start date",
                             "an additional fee applies to onboarding"],
    },
    {
        "id": "sal-004",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "request_information",
        "requires_human_review": False,
        "incoming": {
            "from": "hello@unknown-startup.io",
            "subject": "Interested",
            "received_at": "2025-05-13T15:40:00Z",
            "body": "Hi, interested in your product. How much?",
        },
        "gold_reply": {
            "subject": "Re: Interested",
            "body": (
                "Hello,\n\nThank you for getting in touch.\n\nRelay is priced per seat and the "
                "tier depends on volume, so a single figure would be misleading. In order to "
                "give you an accurate number I need to know roughly how many users you expect, "
                "which systems you would be connecting, and your expected monthly record "
                "volume.\n\nOur entry tier begins at 9 pounds per seat per month, so that gives "
                "you an order of magnitude in the meantime.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "how many users you expect",
            "which systems you would be connecting",
            "entry tier begins at 9 pounds per seat per month",
        ],
        "must_not_include": ["the total cost is", "we cannot provide pricing"],
    },
    {
        "id": "sal-005",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "director@tidewater-partners.com",
            "subject": "Reseller arrangement",
            "received_at": "2025-05-14T08:30:00Z",
            "body": (
                "Margaret, we would like to resell Relay into the public sector at a 40 per "
                "cent margin, with exclusivity in the UK.\n\nTidewater Partners"
            ),
        },
        "gold_reply": {
            "subject": "Re: Reseller arrangement",
            "body": (
                "Hello,\n\nThank you for the proposal and for your confidence in the "
                "product.\n\nI am not able to offer UK exclusivity. We already work with two "
                "partners in this market and an exclusive arrangement would require us to "
                "terminate existing agreements, which we will not do.\n\nOur standard partner "
                "programme offers a 25 per cent margin with deal registration protection, which "
                "in practice protects the opportunities you source. If that is of interest I "
                "will send the partner agreement for your review.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to offer UK exclusivity",
            "we already work with two partners in this market",
            "25 per cent margin with deal registration protection",
        ],
        "must_not_include": ["exclusivity is granted", "we accept a 40 per cent margin"],
    },
    {
        "id": "sal-006",
        "category": "sales",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "legal@ridgeline-utilities.com",
            "subject": "Redlines to your MSA",
            "received_at": "2025-05-14T14:00:00Z",
            "body": (
                "Margaret, attached are our redlines. We require unlimited liability for data "
                "breach, a 99.99 per cent SLA and source code escrow. Please confirm "
                "acceptance so we can sign this week.\n\nRidgeline Legal"
            ),
        },
        "gold_reply": {
            "subject": "Re: Redlines to your MSA",
            "body": (
                "Hello,\n\nThank you for sending the redlines.\n\nI am not able to confirm "
                "acceptance of these terms. Unlimited liability, the availability commitment "
                "and source code escrow each require review by our legal counsel and, in the "
                "case of the SLA, by our operations team.\n\nI have passed the document to "
                "Karim Aslan, your account director, and to our counsel today. Karim will "
                "come back to you with a marked up response and will be your point of contact "
                "on the contract.\n\nI recognise you are working to sign this week and I have "
                "made that timeline clear internally.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to confirm acceptance of these terms",
            "passed the document to Karim Aslan and to our counsel",
            "Karim will come back with a marked up response",
        ],
        "must_not_include": [
            "we accept unlimited liability",
            "we agree to the 99.99 per cent SLA",
            "source code escrow is agreed",
        ],
    },
    {
        "id": "sal-007",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": False,
        "incoming": {
            "from": "innovation@savannah-telecom.za",
            "subject": "Do you have a roadmap for Kafka support?",
            "received_at": "2025-05-15T09:00:00Z",
            "body": (
                "Margaret, native Kafka support would be decisive for us. Is it on the "
                "roadmap and when?\n\nSavannah Telecom"
            ),
        },
        "gold_reply": {
            "subject": "Re: Do you have a roadmap for Kafka support?",
            "body": (
                "Hello,\n\nThank you for the question, and I would rather give you an accurate "
                "answer than a convenient one.\n\nNative Kafka support is on the roadmap. I am "
                "not able to give you a delivery date, because our product team does not commit "
                "publicly to dates more than one quarter ahead and I will not put a figure in "
                "writing that I cannot stand behind.\n\nWhat I can do is arrange a call with "
                "our Head of Product, Rhea Balakrishnan, who can talk you through sequencing "
                "and take your requirements directly. Would next week suit?\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "native Kafka support is on the roadmap",
            "I am not able to give you a delivery date",
            "a call with our Head of Product Rhea Balakrishnan",
        ],
        "must_not_include": ["Kafka support ships in Q3", "Kafka support is available today"],
    },
    {
        "id": "sal-008",
        "category": "sales",
        "difficulty": "hard",
        "intent_label": "decline_politely",
        "requires_human_review": True,
        "incoming": {
            "from": "buyer@offshore-holdings-ltd.com",
            "subject": "Urgent purchase - 400 seats, wire transfer today",
            "received_at": "2025-05-15T17:30:00Z",
            "body": (
                "We wish to purchase 400 Relay seats immediately. We will wire the full amount "
                "today from a third party account and require the licences activated within "
                "the hour. Please send bank details. No contract review necessary.\n\n"
                "Offshore Holdings"
            ),
        },
        "gold_reply": {
            "subject": "Re: Urgent purchase - 400 seats, wire transfer today",
            "body": (
                "Hello,\n\nThank you for your interest. I am not able to proceed on the basis "
                "described.\n\nWe do not accept payment from a third party account, and all "
                "orders require a signed agreement and completion of our standard customer "
                "verification before any licence is activated. These requirements apply to "
                "every customer without exception.\n\nIf you would like to proceed "
                "conventionally, I will send our onboarding pack and we can begin verification. "
                "Typical time from signature to activation is two working days.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "we do not accept payment from a third party account",
            "all orders require a signed agreement and customer verification",
            "two working days from signature to activation",
        ],
        "must_not_include": [
            "our bank details are",
            "the licences have been activated",
            "we can waive the verification",
        ],
    },
    {
        "id": "sal-009",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "ops@meridian-parts.jp",
            "subject": "Quote expired before we could approve it",
            "received_at": "2025-05-16T07:45:00Z",
            "body": (
                "Margaret, quote Q-3391 expired on Wednesday while it was still with our "
                "finance committee. Can it be reinstated?\n\nMeridian Parts"
            ),
        },
        "gold_reply": {
            "subject": "Re: Quote expired before we could approve it",
            "body": (
                "Hello,\n\nOf course. Quote Q-3391 has been reissued with the same pricing and "
                "a new expiry date of 30 June, which should give your finance committee "
                "sufficient time.\n\nThe reference is unchanged so your internal approval "
                "papers remain valid. There is no need to restart your process.\n\nPlease let "
                "me know if a longer validity period would be helpful.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "Q-3391 has been reissued with the same pricing",
            "new expiry date of 30 June",
            "the reference is unchanged",
        ],
        "must_not_include": ["pricing has increased on the reissued quote",
                             "the quote cannot be reinstated"],
    },
    {
        "id": "sal-010",
        "category": "sales",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "cio@orchid-health.com",
            "subject": "Is Relay suitable for patient data?",
            "received_at": "2025-05-16T12:20:00Z",
            "body": (
                "Margaret, we would be moving records that include patient identifiers. Is "
                "Relay appropriate and what assurances can you give?\n\nOrchid Health"
            ),
        },
        "gold_reply": {
            "subject": "Re: Is Relay suitable for patient data?",
            "body": (
                "Hello,\n\nThank you for raising this at the evaluation stage.\n\nRelay is used "
                "by healthcare customers and supports encryption in transit and at rest, field "
                "level redaction, and UK data residency on the Scale tier. We hold ISO 27001 "
                "and SOC 2 Type II, and we will sign a Data Processing Agreement including "
                "standard contractual clauses.\n\nI would not want to assert that Relay is "
                "appropriate for your specific use case without your clinical governance team "
                "reviewing it. I can arrange a session between them and our security lead, Ana "
                "Duarte, which is the sensible next step.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "encryption in transit and at rest",
            "UK data residency on the Scale tier",
            "ISO 27001 and SOC 2 Type II",
            "a session with our security lead Ana Duarte",
        ],
        "must_not_include": [
            "Relay is fully compliant for your use case",
            "no further review is necessary",
        ],
    },
    # ---------------------------------------------------------------- recruiting
    {
        "id": "rec-001",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "confirm_and_commit",
        "requires_human_review": False,
        "incoming": {
            "from": "amelia.frost@gmail.com",
            "subject": "Field Engineer application - interview availability",
            "received_at": "2025-05-19T08:00:00Z",
            "body": (
                "Hello Margaret, thank you for progressing my application. I am available any "
                "afternoon next week except Wednesday.\n\nAmelia Frost"
            ),
        },
        "gold_reply": {
            "subject": "Re: Field Engineer application - interview availability",
            "body": (
                "Dear Amelia,\n\nThank you for your flexibility. I have scheduled your "
                "interview for Tuesday 27 May at 14:00, lasting approximately 60 minutes.\n\n"
                "You will meet Dan Whitfield, our Operations Manager, and one member of the "
                "field team. The session is competency based and there is no technical test "
                "to prepare for.\n\nA calendar invitation with the video link follows "
                "separately.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "Tuesday 27 May at 14:00",
            "approximately 60 minutes",
            "you will meet Dan Whitfield",
            "there is no technical test",
        ],
        "must_not_include": ["please prepare a presentation", "we will be in touch to arrange a date"],
    },
    {
        "id": "rec-002",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "decline_politely",
        "requires_human_review": False,
        "incoming": {
            "from": "p.mensah@outlook.com",
            "subject": "Following up on my application",
            "received_at": "2025-05-19T14:00:00Z",
            "body": (
                "Hello, I interviewed for the Field Engineer role on 6 May and have not heard "
                "back. Could you update me?\n\nPatience Mensah"
            ),
        },
        "gold_reply": {
            "subject": "Re: Following up on my application",
            "body": (
                "Dear Patience,\n\nThank you for following up, and I apologise that you had to "
                "chase us.\n\nOn this occasion we will not be progressing your application. The "
                "panel felt that the role needed more hands on experience with industrial "
                "network hardware than your background currently shows, and we appointed a "
                "candidate who had worked in that environment directly.\n\nYour interview was "
                "strong on customer handling and the panel said so. If a more customer facing "
                "role opens I would be glad to contact you, and I will keep your details on "
                "file for twelve months with your permission.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "we will not be progressing your application",
            "more hands on experience with industrial network hardware",
            "keep your details on file for twelve months",
        ],
        "must_not_include": ["we would like to offer you the role",
                             "you have been invited to a second interview"],
    },
    {
        "id": "rec-003",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "j.kovac@protonmail.com",
            "subject": "Question about the Support Engineer role",
            "received_at": "2025-05-20T09:30:00Z",
            "body": (
                "Hello, before applying I would like to know whether the Support Engineer role "
                "involves an on call rota and whether it is remote.\n\nJan Kovac"
            ),
        },
        "gold_reply": {
            "subject": "Re: Question about the Support Engineer role",
            "body": (
                "Dear Jan,\n\nThank you for asking before applying rather than after.\n\nThe "
                "role does include an on call rota. It operates one week in six, and on call "
                "weeks are compensated at 200 pounds plus time off in lieu for any callout "
                "outside working hours.\n\nThe role is hybrid rather than fully remote. We ask "
                "for two days per week in our Manchester office, and the on call weeks can be "
                "worked entirely from home.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "on call operates one week in six",
            "compensated at 200 pounds plus time off in lieu",
            "two days per week in our Manchester office",
        ],
        "must_not_include": ["the role is fully remote with no office days",
                             "there is no on call requirement"],
    },
    {
        "id": "rec-004",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "negotiate_alternative",
        "requires_human_review": False,
        "incoming": {
            "from": "amelia.frost@gmail.com",
            "subject": "Re: Offer - Field Engineer",
            "received_at": "2025-05-20T16:45:00Z",
            "body": (
                "Margaret, thank you for the offer. I was hoping for 46,000 rather than 42,000. "
                "Is there flexibility?\n\nAmelia"
            ),
        },
        "gold_reply": {
            "subject": "Re: Offer - Field Engineer",
            "body": (
                "Dear Amelia,\n\nThank you for coming back to me directly, and for being "
                "specific about the figure.\n\nI am not able to reach 46,000 for this role. The "
                "band for Field Engineer runs to 44,000 and going beyond it would place you "
                "above colleagues with more service, which I am not willing to do.\n\nI can "
                "offer 44,000, which is the top of the band, together with an early salary "
                "review at six months rather than the usual twelve.\n\nPlease take the time you "
                "need. I can hold the offer open until 30 May.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to reach 46,000",
            "the band runs to 44,000",
            "an early salary review at six months",
            "hold the offer open until 30 May",
        ],
        "must_not_include": ["I can offer 46,000", "the offer is withdrawn"],
    },
    {
        "id": "rec-005",
        "category": "recruiting",
        "difficulty": "hard",
        "intent_label": "decline_politely",
        "requires_human_review": True,
        "incoming": {
            "from": "d.whitfield.friend@gmail.com",
            "subject": "My nephew for the field engineer job",
            "received_at": "2025-05-21T08:15:00Z",
            "body": (
                "Margaret, Dan mentioned you are hiring field engineers. My nephew is looking "
                "for work and would be perfect. Could you skip him to the final round? CV "
                "attached.\n\nRegards"
            ),
        },
        "gold_reply": {
            "subject": "Re: My nephew for the field engineer job",
            "body": (
                "Hello,\n\nThank you for thinking of us, and please do encourage him to "
                "apply.\n\nI am not able to move any candidate directly to the final round. "
                "Every applicant goes through the same screening and first interview, and "
                "making an exception would be unfair to the others and would undermine the "
                "process for the person concerned.\n\nThe role is advertised at "
                "northwind.io/careers and applications there reach me directly. He is very "
                "welcome to apply on that basis.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to move any candidate directly to the final round",
            "every applicant goes through the same screening and first interview",
            "northwind.io/careers",
        ],
        "must_not_include": [
            "I have added him to the final round",
            "send me his CV and I will fast track it",
        ],
    },
    {
        "id": "rec-006",
        "category": "recruiting",
        "difficulty": "hard",
        "intent_label": "request_information",
        "requires_human_review": True,
        "incoming": {
            "from": "hiring@competitor-relay-alt.com",
            "subject": "Reference request - Aisha Kone",
            "received_at": "2025-05-21T13:00:00Z",
            "body": (
                "Hello, we are considering Aisha Kone for a role and would like a reference. "
                "Could you tell us why she is leaving, her salary, and whether you would "
                "rehire her?\n\nTalent Team"
            ),
        },
        "gold_reply": {
            "subject": "Re: Reference request - Aisha Kone",
            "body": (
                "Hello,\n\nThank you for your enquiry. I am not able to respond to a reference "
                "request received in this way.\n\nWe provide references only on receipt of the "
                "candidate's written consent, and we provide factual references only: job "
                "title, dates of employment and reason for leaving where the employee has "
                "agreed to its disclosure. We do not disclose salary.\n\nIf you send the "
                "signed consent to hr@northwind.io I will action the request within three "
                "working days.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am not able to respond to a reference request received in this way",
            "only on receipt of written consent",
            "we do not disclose salary",
            "hr@northwind.io",
        ],
        "must_not_include": [
            "she is leaving because",
            "her salary is",
            "we would rehire her",
        ],
    },
    {
        "id": "rec-007",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "apologize_and_remediate",
        "requires_human_review": False,
        "incoming": {
            "from": "s.varga@fastmail.com",
            "subject": "Nobody attended my interview",
            "received_at": "2025-05-22T09:00:00Z",
            "body": (
                "Margaret, I waited on the video call for 25 minutes yesterday and nobody "
                "joined. I took unpaid leave for this.\n\nSofia Varga"
            ),
        },
        "gold_reply": {
            "subject": "Re: Nobody attended my interview",
            "body": (
                "Dear Sofia,\n\nI am very sorry. That should not have happened and the fault is "
                "entirely ours: the panel was double booked and nobody checked the invitation "
                "before the slot.\n\nI would like to rearrange at a time that suits you, "
                "including outside working hours so that you do not lose pay a second time. I "
                "can offer Thursday 29 May at 18:00 or Saturday morning.\n\nI am also "
                "reimbursing your unpaid leave for yesterday. Please tell me the amount and I "
                "will arrange payment regardless of the outcome of your application.\n\n"
                + SIGNOFF
            ),
        },
        "must_include": [
            "the panel was double booked",
            "Thursday 29 May at 18:00 or Saturday morning",
            "I am reimbursing your unpaid leave",
        ],
        "must_not_include": ["you missed the invitation", "we are withdrawing your application"],
    },
    {
        "id": "rec-008",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": False,
        "incoming": {
            "from": "candidate.lee@gmail.com",
            "subject": "Visa sponsorship question",
            "received_at": "2025-05-22T15:30:00Z",
            "body": (
                "Hello Margaret, I hold a Graduate visa expiring in November. Would Northwind "
                "sponsor a Skilled Worker visa for the Support Engineer role?\n\nWen Lee"
            ),
        },
        "gold_reply": {
            "subject": "Re: Visa sponsorship question",
            "body": (
                "Dear Wen,\n\nThank you for raising this early, which is genuinely helpful.\n\n"
                "Northwind does hold a sponsor licence. Whether we can sponsor this particular "
                "role depends on the salary threshold and the occupation code, and I am not the "
                "right person to give you a definitive answer.\n\nI have referred your question "
                "to our immigration adviser today and asked for a written answer. I expect to "
                "come back to you by 29 May, which is well before your application would need "
                "to progress.\n\nYour application remains active in the meantime.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "Northwind does hold a sponsor licence",
            "referred to our immigration adviser",
            "come back to you by 29 May",
            "your application remains active",
        ],
        "must_not_include": [
            "we will sponsor your visa",
            "we do not sponsor visas",
            "your application cannot proceed",
        ],
    },
    {
        "id": "rec-009",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "acknowledge_and_defer",
        "requires_human_review": False,
        "incoming": {
            "from": "amelia.frost@gmail.com",
            "subject": "Start date question",
            "received_at": "2025-05-23T08:40:00Z",
            "body": (
                "Margaret, I have accepted the offer. My notice period is eight weeks but I "
                "may be able to negotiate down. When do you need me?\n\nAmelia"
            ),
        },
        "gold_reply": {
            "subject": "Re: Start date question",
            "body": (
                "Dear Amelia,\n\nCongratulations again, and thank you for the update.\n\nEight "
                "weeks is entirely workable and I would not want you to leave your current "
                "employer on poor terms in order to start sooner. Please serve whatever notice "
                "is right.\n\nI will confirm the formal start date once you have given notice "
                "and know your last working day. Onboarding runs on the first and third Monday "
                "of each month, so we will align to whichever falls first.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "eight weeks is entirely workable",
            "I will confirm the formal start date once you have given notice",
            "onboarding runs on the first and third Monday of each month",
        ],
        "must_not_include": ["you must start within four weeks",
                             "your start date is 1 July"],
    },
    {
        "id": "rec-010",
        "category": "recruiting",
        "difficulty": "hard",
        "intent_label": "escalate_or_handoff",
        "requires_human_review": True,
        "incoming": {
            "from": "s.varga@fastmail.com",
            "subject": "Concern about interview questions",
            "received_at": "2025-05-23T16:00:00Z",
            "body": (
                "Margaret, at my rearranged interview one of the panel asked whether I planned "
                "to have children. I found this inappropriate and it affected how I "
                "performed.\n\nSofia Varga"
            ),
        },
        "gold_reply": {
            "subject": "Re: Concern about interview questions",
            "body": (
                "Dear Sofia,\n\nThank you for telling me. That question should not have been "
                "asked and I am sorry that it was.\n\nI am not going to investigate this myself, "
                "because I sit on the hiring panel and it would not be an independent review. I "
                "have referred it to our HR lead, Nadia Farrell, who will look into it and "
                "contact you directly.\n\nSeparately, I do not want the interview to stand as "
                "the basis of a decision. I would like to offer you a fresh interview with a "
                "different panel, and no decision will be taken on your application until you "
                "have had one.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "that question should not have been asked",
            "referred to our HR lead Nadia Farrell",
            "a fresh interview with a different panel",
            "no decision will be taken until you have had one",
        ],
        "must_not_include": [
            "the question was appropriate",
            "your performance was the reason",
            "I have spoken to the panel member",
        ],
    },
    {
        "id": "rec-011",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "resolve_with_action",
        "requires_human_review": False,
        "incoming": {
            "from": "agency@apexsearch-partners.com",
            "subject": "Invoice for placement of A. Frost",
            "received_at": "2025-05-26T10:00:00Z",
            "body": (
                "Margaret, our invoice for the placement of Amelia Frost at 20 per cent of "
                "salary is attached. Payment terms 14 days.\n\nApex Search"
            ),
        },
        "gold_reply": {
            "subject": "Re: Invoice for placement of A. Frost",
            "body": (
                "Hello,\n\nThank you for the invoice. I am unable to pay it as presented.\n\n"
                "Amelia Frost applied directly through our careers page on 2 May, which is "
                "recorded in our applicant tracking system, and predates your introduction of "
                "9 May. Our terms provide that a fee is payable only where the agency made the "
                "first introduction.\n\nI have attached the application record. If you believe "
                "this is mistaken, please send your evidence of first contact and I will review "
                "it promptly.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "I am unable to pay it as presented",
            "applied directly through our careers page on 2 May",
            "predates your introduction of 9 May",
        ],
        "must_not_include": ["payment will be made within 14 days", "we accept the placement fee"],
    },
    {
        "id": "rec-012",
        "category": "recruiting",
        "difficulty": "normal",
        "intent_label": "provide_information",
        "requires_human_review": False,
        "incoming": {
            "from": "careers.query@gmail.com",
            "subject": "Do you take apprentices?",
            "received_at": "2025-05-26T14:30:00Z",
            "body": (
                "Hello, I am 18 and finishing college. Do you offer apprenticeships in "
                "IT?\n\nDaniel"
            ),
        },
        "gold_reply": {
            "subject": "Re: Do you take apprentices?",
            "body": (
                "Dear Daniel,\n\nThank you for writing, and it is good to see you looking "
                "early.\n\nWe take two apprentices each year on a Level 3 Information "
                "Communications Technician standard, and recruitment opens in July for a "
                "September start. No prior experience is required.\n\nThe roles are advertised "
                "at northwind.io/careers and also through the Manchester Digital apprenticeship "
                "scheme. If you send me your email address I will make sure you hear when the "
                "advert goes live.\n\n" + SIGNOFF
            ),
        },
        "must_include": [
            "two apprentices each year",
            "Level 3 Information Communications Technician",
            "recruitment opens in July for a September start",
            "northwind.io/careers",
        ],
        "must_not_include": ["we do not offer apprenticeships", "prior experience is required"],
    },
]
