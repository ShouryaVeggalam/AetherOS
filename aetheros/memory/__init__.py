"""Long-term Operational Memory — verified system knowledge only.

Not chatbot memory. Never stores conversations, files, prompts, or personal data.
"""

from __future__ import annotations

from aetheros.memory.consolidation import consolidate_records, title_similarity
from aetheros.memory.engine import MemoryEngine
from aetheros.memory.formatter import OperationalMemoryPanel
from aetheros.memory.models import MemoryQuery, MemoryRecord, Pattern
from aetheros.memory.retrieval import related, retrieve, similar_patterns
from aetheros.memory.store import OperationalMemoryStore
from aetheros.memory.verifier import (
    MemoryCandidate,
    VerificationOutcome,
    verify_candidate,
)

__all__ = [
    "MemoryCandidate",
    "MemoryEngine",
    "MemoryQuery",
    "MemoryRecord",
    "OperationalMemoryPanel",
    "OperationalMemoryStore",
    "Pattern",
    "VerificationOutcome",
    "consolidate_records",
    "related",
    "retrieve",
    "similar_patterns",
    "title_similarity",
    "verify_candidate",
]
