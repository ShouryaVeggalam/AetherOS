"""Research journal — append-only immutable experiment log.

No editing of previous entries. Twin-research provenance only.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.research_ai.models import (
    Experiment,
    ExperimentOutcome,
    JournalEntry,
    Result,
)


class ResearchJournal:
    """Append-only journal of experiment outcomes."""

    def __init__(self) -> None:
        self._entries: list[JournalEntry] = []

    def append(
        self,
        *,
        experiment: Experiment,
        outcome: ExperimentOutcome,
        reproducibility: float,
        note: str = "",
        now: datetime | None = None,
    ) -> JournalEntry:
        """Append one immutable journal entry."""

        entry = JournalEntry(
            experiment_id=experiment.id,
            hypothesis_id=experiment.hypothesis.id,
            timestamp=now or datetime.now(UTC),
            outcome=outcome,
            reproducibility=reproducibility,
            note=note,
        )
        self._entries.append(entry)
        return entry

    def record_result(
        self,
        experiment: Experiment,
        result: Result,
        *,
        accepted: bool,
        now: datetime | None = None,
    ) -> JournalEntry:
        """Convenience: map verification outcome to a journal row."""

        outcome: ExperimentOutcome
        if accepted:
            outcome = "supported"
        elif result.reproducibility < 50.0:
            outcome = "rejected"
        else:
            outcome = "inconclusive"
        return self.append(
            experiment=experiment,
            outcome=outcome,
            reproducibility=result.reproducibility,
            note=f"confidence={result.confidence:.1f}; stability={result.stability:.1f}",
            now=now,
        )

    def entries(self, *, limit: int = 100) -> tuple[JournalEntry, ...]:
        """Return newest-last entries (immutable copy)."""

        if limit <= 0:
            return ()
        return tuple(self._entries[-limit:])

    def __len__(self) -> int:
        return len(self._entries)
