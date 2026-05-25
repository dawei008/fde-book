"""ch13-guardrails state — guardrail id + version shared across scripts.

Saved to data/ch13-state.json after `make up`. Used by run.py to invoke
Converse with the guardrail attached, and by down.py to delete the
guardrail (versions go away with the guardrail).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parents[2]
STATE_FILE = DEMO_DIR / "data" / "ch13-state.json"

# Stable resource names (deterministic; one demo per account/region).
GUARDRAIL_NAME = "fde_book_ch13_guardrail"

# We use haiku-4.5 because it's cheap, fast, and supported by Converse +
# Guardrails. Cross-region inference profile.
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

# Messages the guardrail returns when input/output is blocked (visible
# in Converse output as the assistant message when stopReason is
# guardrail_intervened).
BLOCKED_INPUT_MSG = "Sorry, the model can't help with that input."
BLOCKED_OUTPUT_MSG = "Sorry, the model can't return that output."


def guardrail_config() -> dict:
    """The actual policy. Four layers:

    1. PII filter: phone/email/name ANONYMIZE (replace with token);
       a regex for China resident ID card BLOCK (resident IDs are
       sensitive enough that we never want to even respond).
    2. Denied topic: "off_scope_chat" — Hesheng's overseas service desk
       only handles ticket triage, not creative writing or chit-chat.
    3. Content filter: PROMPT_ATTACK at HIGH (jailbreaks, prompt
       injection); VIOLENCE at MEDIUM (industrial machine context;
       a brief mention of force/torque is fine, gore is not).
    4. Contextual grounding: threshold 0.7 — only relevant when we
       wire in source documents; included so Ch13 13.3 has all four
       layers represented.

    Note: the boto3 schema uses snakeCamel keys (e.g. piiEntitiesConfig).
    """
    return {
        "sensitiveInformationPolicyConfig": {
            "piiEntitiesConfig": [
                {"type": "PHONE", "action": "ANONYMIZE"},
                {"type": "EMAIL", "action": "ANONYMIZE"},
                {"type": "NAME", "action": "ANONYMIZE"},
                {"type": "ADDRESS", "action": "ANONYMIZE"},
            ],
            "regexesConfig": [{
                "name": "china_id_card",
                "description": "PRC resident ID card (18 digits, last char 0-9 or X)",
                # 17 digits + 1 of [0-9X] is the canonical PRC ID format.
                "pattern": r"\b\d{17}[\dXx]\b",
                "action": "BLOCK",
            }],
        },
        "topicPolicyConfig": {
            "topicsConfig": [{
                "name": "off_scope_chat",
                "definition": (
                    "Creative writing, poetry, songs, role-play, or "
                    "general chit-chat unrelated to industrial servo "
                    "motor / robot ticket triage."
                ),
                "examples": [
                    "Write me a poem about servo motors.",
                    "Tell me a joke about robotics.",
                    "Write a song about manufacturing.",
                ],
                "type": "DENY",
            }],
        },
        "contentPolicyConfig": {
            "filtersConfig": [
                {"type": "PROMPT_ATTACK", "inputStrength": "HIGH",
                 "outputStrength": "NONE"},
                {"type": "VIOLENCE", "inputStrength": "MEDIUM",
                 "outputStrength": "MEDIUM"},
            ],
        },
        "contextualGroundingPolicyConfig": {
            "filtersConfig": [
                {"type": "GROUNDING", "threshold": 0.7},
                {"type": "RELEVANCE", "threshold": 0.7},
            ],
        },
    }


@dataclass
class State:
    guardrail_id: str = ""
    guardrail_arn: str = ""
    guardrail_version: str = ""

    def save(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls) -> "State":
        if not STATE_FILE.exists():
            raise FileNotFoundError(
                f"No state file. Run `make up` first.\nExpected: {STATE_FILE}"
            )
        return cls(**json.loads(STATE_FILE.read_text()))

    @classmethod
    def load_or_empty(cls) -> "State":
        if STATE_FILE.exists():
            return cls.load()
        return cls()
