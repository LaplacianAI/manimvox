"""Spoken respellings: applied to what the voice says, never to subtitles."""

from __future__ import annotations

import re

BUILTIN: list[tuple[str, str]] = [
    (r"(?<=[a-z])_(?=[a-z])", " "),  # snake_case reads as words first, so get_user_id → get user id → … I D
    (r"\bAPIs\b", "A P I's"),
    (r"\bAPI\b", "A P I"),
    (r"\bLLMs\b", "L L Ms"),
    (r"\bLLM\b", "L L M"),
    (r"\bUI\b", "U I"),
    (r"\bURLs\b", "U R Ls"),
    (r"\bURL\b", "U R L"),
    (r"\bHTTPS\b", "H T T P S"),
    (r"\bHTTP\b", "H T T P"),
    (r"\bJSON\b", "jason"),
    (r"\bSQL\b", "sequel"),
    (r"\bCLI\b", "C L I"),
    (r"\bSDK\b", "S D K"),
    (r"\bJWT\b", "J W T"),
    (r"\bSSE\b", "S S E"),
    (r"\bDB\b", "database"),
    (r"\b[Ii][Dd]\b", "I D"),
    (r"\bIDs\b", "I Ds"),
    (r"\bPDF\b", "P D F"),
    (r"\bOAuth\b", "oh auth"),
    (r"\bOIDC\b", "O I D C"),
    (r"\bRBAC\b", "R back"),
    (r"\bMCP\b", "M C P"),
    (r"\bRAG\b", "rag"),
    (r"\bAI\b", "A I"),
    (r"\bSaaS\b", "sass"),
    (r"\bnginx\b", "engine x"),
    (r"\bKafka\b", "Kaf-ka"),
    (r"\bMySQL\b", "my sequel"),
    (r"\bPostgres\b", "post gress"),
    (r"\bPostgreSQL\b", "post gress Q L"),
    (r"\bK8s\b", "kubernetes"),
    (r"\b401\b", "four oh one"),
    (r"\b403\b", "four oh three"),
    (r"\b404\b", "four oh four"),
]


def spoken_form(text: str, extra: list[tuple[str, str]] = ()) -> str:
    for pat, rep in extra:
        try:
            text = re.sub(pat, rep, text)
        except re.error as e:
            raise ValueError(f"pron rule '{pat}' in series.json is not a valid regex: {e}") from e
    for pat, rep in BUILTIN:
        text = re.sub(pat, rep, text)
    return text
