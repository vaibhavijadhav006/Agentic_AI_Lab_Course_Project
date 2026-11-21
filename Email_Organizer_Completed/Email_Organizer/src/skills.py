import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .models import Email, EmailAnalysis, Draft
from .llm import LLMClient


class EmailSkills:
    """Lab 3: reusable email skills."""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()

    # ---------------------------------------------------------
    # SKILL 1: EMAIL CLASSIFICATION
    # ---------------------------------------------------------
    def classify_email(self, email: Email) -> EmailAnalysis:

        result = self.llm.classify(
            email.subject,
            email.body
        )

        if result:
            return EmailAnalysis(
                email_id=email.id,
                category=result.get("category", "other"),
                priority=result.get("priority", "MEDIUM"),
                urgency_score=int(
                    result.get("urgency_score", 50)
                ),
                action_items=result.get(
                    "action_items", []
                ),
                follow_up_date=result.get(
                    "follow_up_date"
                ),
                reply_required=bool(
                    result.get("reply_required", False)
                ),
                reason=result.get(
                    "reason",
                    "LLM classification"
                )
            )

        # Local fallback
        text = (
            f"{email.subject} {email.body}"
        ).lower()

        if any(
            k in text
            for k in ["placement", "registration"]
        ):
            category = "placement"

        elif any(
            k in text
            for k in [
                "assignment",
                "project",
                "research",
                "paper",
                "lab",
                "course",
                "exam",
                "report"
            ]
        ):
            category = "academic"

        elif any(
            k in text
            for k in ["meeting", "review"]
        ):
            category = "meeting"

        elif any(
            k in text
            for k in ["minutes", "department"]
        ):
            category = "administrative"

        else:
            category = "information"

        # Urgency detection
        urgent_words = [
            "urgent",
            "action required",
            "tomorrow",
            "deadline",
            "today",
            "by friday",
            "before friday",
            "by tomorrow",
            "before tomorrow",
            "must complete",
            "must submit"
        ]

        hits = sum(
            1
            for word in urgent_words
            if word in text
        )

        if hits >= 2:
            priority = "HIGH"
            score = 85

        elif hits == 1:
            priority = "MEDIUM"
            score = 60

        else:
            priority = "LOW"
            score = 25

        action_items = self.extract_action_items(
            email
        )

        # Decide whether a reply is needed
        reply_required = any(
            marker in text
            for marker in [
                "reply",
                "respond",
                "can you",
                "could you",
                "please clarify",
                "confirm"
            ]
        )

        follow_up_date = None

        if "tomorrow" in text:
            follow_up_date = (
                datetime.now()
                + timedelta(days=1)
            ).date().isoformat()

        return EmailAnalysis(
            email_id=email.id,
            category=category,
            priority=priority,
            urgency_score=score,
            action_items=action_items,
            follow_up_date=follow_up_date,
            reply_required=reply_required,
            reason=(
                "Rule-based classification; "
                f"urgency keyword hits={hits}"
            )
        )

    # ---------------------------------------------------------
    # SKILL 2: PRIORITY
    # ---------------------------------------------------------
    def score_priority(
        self,
        email: Email,
        analysis: EmailAnalysis
    ) -> EmailAnalysis:

        text = (
            f"{email.subject} {email.body}"
        ).lower()

        if any(
            k in text
            for k in [
                "action required",
                "deadline",
                "must complete",
                "must submit"
            ]
        ):
            analysis.priority = "HIGH"

            analysis.urgency_score = max(
                analysis.urgency_score,
                85
            )

        if any(
            k in text
            for k in [
                "urgent",
                "immediately",
                "today"
            ]
        ):
            analysis.priority = "CRITICAL"

            analysis.urgency_score = max(
                analysis.urgency_score,
                95
            )

        return analysis

    # ---------------------------------------------------------
    # SKILL 3: ACTION ITEM EXTRACTION
    # ---------------------------------------------------------
    def extract_action_items(
        self,
        email: Email
    ) -> List[str]:

        text = email.body.strip()

        items = []

        sentences = re.split(
            r'(?<=[.!?])\s+',
            text
        )

        ignored_phrases = [
            "here are some papers",
            "for your reference",
            "no immediate action is required",
            "for your information",
            "attached for your reference"
        ]

        def add_item(value):

            value = value.strip(
                " .,!?:;"
            )

            if not value:
                return

            existing = {
                x.lower()
                for x in items
            }

            if value.lower() not in existing:
                items.append(value)

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            lower = sentence.lower()

            # Ignore informational sentences
            if any(
                phrase in lower
                for phrase in ignored_phrases
            ):
                continue

            # -----------------------------------------
            # Please submit / complete / send...
            # -----------------------------------------
            match = re.search(
                r'\bplease\s+'
                r'(submit|complete|send|reply|respond|'
                r'confirm|register|prepare|review|'
                r'clarify|bring)\s+(.+)',
                sentence,
                flags=re.IGNORECASE
            )

            if match:

                action = (
                    f"{match.group(1)} "
                    f"{match.group(2)}"
                )

                parts = re.split(
                    r'\s+and\s+(?=be ready\b)',
                    action,
                    flags=re.IGNORECASE
                )

                for part in parts:
                    add_item(part)

            # -----------------------------------------
            # Must complete / submit...
            # -----------------------------------------
            match = re.search(
                r'\bmust\s+'
                r'(submit|complete|send|reply|respond|'
                r'confirm|register|prepare|review)\s+(.+)',
                sentence,
                flags=re.IGNORECASE
            )

            if match:

                add_item(
                    f"{match.group(1)} "
                    f"{match.group(2)}"
                )

            # -----------------------------------------
            # Can you / Could you...
            # -----------------------------------------
            match = re.search(
                r'\b(can you|could you|would you)\s+(.+)',
                sentence,
                flags=re.IGNORECASE
            )

            if match:
                add_item(
                    match.group(2)
                )

            # -----------------------------------------
            # Reply if...
            # -----------------------------------------
            match = re.search(
                r'\breply\s+if\s+(.+)',
                sentence,
                flags=re.IGNORECASE
            )

            if match:
                add_item(
                    f"Reply if {match.group(1)}"
                )

            # -----------------------------------------
            # Be ready...
            # -----------------------------------------
            match = re.search(
                r'\bbe ready\s+(.+)',
                sentence,
                flags=re.IGNORECASE
            )

            if match:
                add_item(
                    f"Be ready {match.group(1)}"
                )

        return items[:5]

    # ---------------------------------------------------------
    # SKILL 4: DRAFT REPLY
    # ---------------------------------------------------------
    def draft_reply(
        self,
        email: Email,
        analysis: EmailAnalysis,
        context: str = ""
    ) -> Draft:

        llm_body = self.llm.draft_reply(
            email.sender,
            email.subject,
            email.body,
            context
        )

        if llm_body:

            body = llm_body.strip()

        else:

            sender = email.sender.lower()

            if "placement" in sender:
                greeting = "Dear Placement Team,"

            elif "hod" in sender:
                greeting = "Dear Sir/Madam,"

            elif (
                "prof" in sender
                or "faculty" in sender
            ):
                greeting = "Dear Professor,"

            else:
                greeting = "Dear Sir/Madam,"

            if analysis.reply_required:

                body = (
                    f"{greeting}\n\n"
                    f"Thank you for your email regarding "
                    f"'{email.subject}'. "
                    f"I have noted the request and will "
                    f"follow the instructions provided.\n\n"
                    f"Regards,\n"
                    f"Student"
                )

            else:

                body = (
                    f"{greeting}\n\n"
                    f"Thank you for sharing the information.\n\n"
                    f"Regards,\n"
                    f"Student"
                )

        return Draft(
            email_id=email.id,
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=body,
            status="PENDING_APPROVAL"
        )

    # ---------------------------------------------------------
    # SKILL 5: FOLLOW-UP DIGEST
    # ---------------------------------------------------------
    def build_followup_digest(
        self,
        analyses: List[EmailAnalysis]
    ) -> List[Dict[str, Any]]:

        result = []

        for analysis in analyses:

            if (
                analysis.follow_up_date
                or analysis.priority in {
                    "HIGH",
                    "CRITICAL"
                }
            ):

                result.append({
                    "email_id": analysis.email_id,
                    "follow_up_date": (
                        analysis.follow_up_date
                    ),
                    "priority": (
                        analysis.priority
                    ),
                    "action_items": (
                        analysis.action_items
                    )
                })

        return result