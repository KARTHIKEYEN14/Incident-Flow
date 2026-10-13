"""Catalogue manager for test fingerprints, round-robin selection, and history persistence."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from pydantic import BaseModel, Field

from incidentflow_testkit.ai_generator import ProposedTestScenario
from incidentflow_testkit.config import TestkitSettings, get_settings


def compute_scenario_fingerprint(scenario: ProposedTestScenario) -> str:
    """
    Compute a deterministic, stable fingerprint based on semantic content:
    endpoint + method + expected status + category + sorted input keys.
    Superficial renames or rewordings produce the exact same fingerprint.
    """
    raw_keys = sorted(scenario.input_data.keys()) if isinstance(scenario.input_data, dict) else []
    # Normalize endpoint removing trailing slash and parameters
    norm_ep = scenario.target_endpoint.split("?")[0].rstrip("/").lower()
    norm_method = scenario.http_method.strip().upper()
    norm_cat = scenario.category.strip().lower()
    norm_status = str(scenario.expected_status_code)

    payload = f"{norm_cat}|{norm_ep}|{norm_method}|{norm_status}|{','.join(raw_keys)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class CataloguedScenario(BaseModel):
    scenario_id: str
    fingerprint: str
    scenario: ProposedTestScenario
    batch_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerationBatch(BaseModel):
    batch_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_used: str
    scenarios: list[CataloguedScenario] = Field(default_factory=list)


class GenerationHistory(BaseModel):
    seen_fingerprints: list[str] = Field(default_factory=list)
    recent_batches: list[str] = Field(default_factory=list)
    feature_rotation_offset: int = 0
    cycle_count: int = 1


class TestCatalogue:
    """Manages scenario deduplication, round-robin selection, and history persistence."""
    __test__ = False

    def __init__(self, settings: TestkitSettings | None = None):
        self.settings = settings or get_settings()
        self.history_file = self.settings.history_file
        self.history = self._load_history()

    def _load_history(self) -> GenerationHistory:
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return GenerationHistory.model_validate(data)
            except Exception:
                pass
        return GenerationHistory()

    def save_history(self) -> None:
        """Persist generation history to disk."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history.model_dump(mode="json"), f, indent=2)

    def select_batch(
        self,
        candidate_scenarios: list[ProposedTestScenario],
        model_name: str,
        limit: int | None = None,
    ) -> tuple[GenerationBatch, str]:
        """
        Process proposed scenarios:
        1. Reject duplicates within the candidate batch.
        2. Filter out already-seen scenarios using fingerprints.
        3. Round-robin select across distinct features.
        4. Select at most `limit` (default 5, up to 10).
        5. Persist history and return the final GenerationBatch.
        """
        max_items = limit or self.settings.max_tests_per_batch
        max_items = min(max(1, max_items), 10)  # Bound strictly between 1 and 10

        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        # Deduplicate candidates within current batch
        unique_candidates: list[tuple[str, ProposedTestScenario]] = []
        batch_seen_fingerprints: set[str] = set()

        for sc in candidate_scenarios:
            fp = compute_scenario_fingerprint(sc)
            if fp not in batch_seen_fingerprints:
                batch_seen_fingerprints.add(fp)
                unique_candidates.append((fp, sc))

        # Check against history
        novel_candidates: list[tuple[str, ProposedTestScenario]] = []
        for fp, sc in unique_candidates:
            if fp not in self.history.seen_fingerprints:
                novel_candidates.append((fp, sc))

        note = ""
        selected_pairs: list[tuple[str, ProposedTestScenario]] = []

        if novel_candidates:
            # Group by category / feature for round-robin balancing
            by_category: dict[str, list[tuple[str, ProposedTestScenario]]] = {}
            for fp, sc in novel_candidates:
                cat = sc.category
                by_category.setdefault(cat, []).append((fp, sc))

            categories = list(by_category.keys())
            # Start round-robin from rotation offset
            offset = self.history.feature_rotation_offset % len(categories) if categories else 0
            ordered_cats = categories[offset:] + categories[:offset]

            # Round robin selection across categories
            while len(selected_pairs) < max_items and any(by_category.values()):
                for cat in ordered_cats:
                    if len(selected_pairs) >= max_items:
                        break
                    if by_category.get(cat):
                        selected_pairs.append(by_category[cat].pop(0))

            # Update rotation offset for next run
            self.history.feature_rotation_offset = (offset + len(selected_pairs)) % (len(categories) or 1)
            note = f"Selected {len(selected_pairs)} fresh scenario(s) across {len(categories)} feature categories."
        else:
            # All available candidate scenarios have been previously seen
            note = (
                f"All {len(unique_candidates)} proposed candidate scenarios match previously generated fingerprints.\n"
                f"The test catalogue has completed cycle #{self.history.cycle_count}.\n"
                f"Advancing to test cycle #{self.history.cycle_count + 1} and recycling catalogue."
            )
            self.history.cycle_count += 1
            # Reset seen fingerprints to allow fresh cycle
            self.history.seen_fingerprints = []
            selected_pairs = unique_candidates[:max_items]

        # Build catalogued scenarios
        catalogued_scenarios: list[CataloguedScenario] = []
        for idx, (fp, sc) in enumerate(selected_pairs, 1):
            scn_id = f"SCN-{idx:03d}"
            catalogued_scenarios.append(
                CataloguedScenario(
                    scenario_id=scn_id,
                    fingerprint=fp,
                    scenario=sc,
                    batch_id=batch_id,
                )
            )
            # Record fingerprint in history
            if fp not in self.history.seen_fingerprints:
                self.history.seen_fingerprints.append(fp)

        # Update history batches
        self.history.recent_batches.append(batch_id)
        if len(self.history.recent_batches) > 50:
            self.history.recent_batches = self.history.recent_batches[-50:]

        self.save_history()

        batch = GenerationBatch(
            batch_id=batch_id,
            model_used=model_name,
            scenarios=catalogued_scenarios,
        )
        return batch, note
