"""Gmail integration — parsing, safety posture, and the mining pairing rule.

No network and no credentials: the Gmail service is a small fake. What matters most here
is the safety posture, which is asserted rather than trusted.
"""

import base64

import pytest

from src.integrations.gmail import (SCOPES, Message, clean_body, create_draft,
                                    inference_time_checks, to_message)


class TestSafetyPosture:
    def test_send_scope_is_never_requested(self):
        """The tool must be *unable* to send, not merely choose not to."""
        joined = " ".join(SCOPES)
        assert "gmail.send" not in joined
        assert "gmail.modify" not in joined
        assert "mail.google.com" not in joined, "full-access scope must never be requested"

    def test_scopes_are_readonly_plus_compose(self):
        assert any(s.endswith("gmail.readonly") for s in SCOPES)
        assert any(s.endswith("gmail.compose") for s in SCOPES)
        assert len(SCOPES) == 2


class TestBodyCleaning:
    def test_strips_quoted_reply_chain(self):
        raw = ("Yes, Tuesday works.\n\n"
               "On Tue, 3 Jun 2025 at 09:14, Dan <d@x.com> wrote:\n"
               "> can you do Tuesday?\n> - Dan\n")
        assert clean_body(raw) == "Yes, Tuesday works."

    def test_strips_original_message_separator(self):
        raw = "Approved.\n\n-----Original Message-----\nFrom: someone\nold text"
        assert clean_body(raw) == "Approved."

    def test_strips_signature_block(self):
        raw = "Confirmed for Friday.\n\n--\nJane Doe\nHead of Ops\n+44 20 7946 0102"
        assert clean_body(raw) == "Confirmed for Friday."

    def test_drops_bare_quoted_lines(self):
        assert clean_body("Agreed.\n> previous line\n> another") == "Agreed."

    def test_empty_input_is_safe(self):
        assert clean_body("") == ""
        assert clean_body(None) == ""


class TestMessageParsing:
    def _raw(self, body: str, sender="a@b.com", labels=None):
        return {
            "id": "m1", "threadId": "t1", "labelIds": labels or ["INBOX"],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "From", "value": sender},
                    {"name": "To", "value": "me@x.com"},
                    {"name": "Subject", "value": "Quarterly review"},
                    {"name": "Date", "value": "Tue, 3 Jun 2025 09:14:00 +0000"},
                    {"name": "Message-ID", "value": "<abc@mail>"},
                ],
                "body": {"data": base64.urlsafe_b64encode(body.encode()).decode()},
            },
        }

    def test_extracts_headers_and_body(self):
        m = to_message(self._raw("Can we move to Thursday?"))
        assert m.subject == "Quarterly review"
        assert m.sender == "a@b.com"
        assert m.body == "Can we move to Thursday?"
        assert m.message_id_header == "<abc@mail>"

    def test_from_me_tracks_the_sent_label(self):
        assert not to_message(self._raw("hi")).from_me
        assert to_message(self._raw("hi", labels=["SENT"])).from_me

    def test_html_only_body_is_stripped_of_tags(self):
        html = "<html><style>p{color:red}</style><p>Hello <b>there</b></p></html>"
        raw = {
            "id": "m", "threadId": "t", "labelIds": [],
            "payload": {
                "mimeType": "text/html",
                "headers": [{"name": "Subject", "value": "s"}],
                "body": {"data": base64.urlsafe_b64encode(html.encode()).decode()},
            },
        }
        body = to_message(raw).body
        assert "Hello" in body and "there" in body
        assert "<b>" not in body and "color:red" not in body


class _FakeDrafts:
    def __init__(self):
        self.created = None

    def create(self, userId, body):
        self.created = {"userId": userId, "body": body}

        class _Exec:
            def execute(_self):
                return {"id": "draft-1"}

        return _Exec()


class _FakeUsers:
    def __init__(self):
        self._drafts = _FakeDrafts()

    def drafts(self):
        return self._drafts


class _FakeService:
    def __init__(self):
        self._users = _FakeUsers()

    def users(self):
        return self._users


class TestDrafting:
    def _msg(self):
        return Message(id="m1", thread_id="t1", sender="a@b.com", to="me@x.com",
                       subject="Renewal terms", body="What's the uplift?",
                       date="", message_id_header="<orig@mail>")

    def test_draft_is_created_in_the_original_thread(self):
        svc = _FakeService()
        create_draft(svc, self._msg(), "Renewal terms", "6% for 24 months.")
        sent = svc.users().drafts().created
        assert sent["body"]["message"]["threadId"] == "t1"

    def test_threading_headers_are_set(self):
        """threadId alone leaves the draft detached in the Gmail UI."""
        svc = _FakeService()
        create_draft(svc, self._msg(), "Renewal terms", "6% for 24 months.")
        raw = svc.users().drafts().created["body"]["message"]["raw"]
        decoded = base64.urlsafe_b64decode(raw).decode()
        assert "In-Reply-To: <orig@mail>" in decoded
        assert "References: <orig@mail>" in decoded

    def test_subject_gets_a_single_re_prefix(self):
        svc = _FakeService()
        create_draft(svc, self._msg(), "Re: Renewal terms", "ok")
        decoded = base64.urlsafe_b64decode(
            svc.users().drafts().created["body"]["message"]["raw"]).decode()
        assert "Subject: Re: Renewal terms" in decoded
        assert "Re: Re:" not in decoded


class TestInferenceTimeChecks:
    def _msg(self, body="Please confirm the RMA number."):
        return Message(id="m", thread_id="t", sender="a@b.com", to="me@x.com",
                       subject="RMA", body=body, date="")

    def test_placeholder_blocks_drafting(self):
        out = inference_time_checks("Hi [CUSTOMER NAME], all sorted.", self._msg())
        assert out["placeholders"] and out["blocking"]

    def test_unsourced_identifier_blocks_drafting(self):
        out = inference_time_checks("Your RMA-7788 is raised.", self._msg())
        assert out["invented_identifiers"] and out["blocking"]

    def test_identifier_present_in_the_incoming_mail_is_fine(self):
        out = inference_time_checks("Your RMA-7788 is raised.",
                                    self._msg("Please chase RMA-7788 for me."))
        assert not out["invented_identifiers"] and not out["blocking"]

    def test_clean_reply_is_not_blocked(self):
        out = inference_time_checks(
            "Thanks for chasing. I have raised the replacement and it ships today.",
            self._msg())
        assert not out["blocking"]

    def test_reports_that_reference_based_scoring_is_unavailable(self):
        out = inference_time_checks("Fine by me.", self._msg())
        assert "known-correct" in out["note"]
