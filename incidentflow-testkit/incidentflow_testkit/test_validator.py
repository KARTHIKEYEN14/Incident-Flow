"""Validator for AI-generated test scenarios against verified IncidentFlow codebase."""

import re
from incidentflow_testkit.ai_generator import ProposedTestScenario
from incidentflow_testkit.feature_discovery import FeatureInventory, discover_incidentflow_features


def _match_route(pattern: str, path: str) -> bool:
    """Check if a concrete path matches a route pattern with {param} placeholders."""
    p_norm = pattern.split("?")[0].rstrip("/").lower()
    t_norm = path.split("?")[0].rstrip("/").lower()

    if p_norm == t_norm:
        return True

    # Convert route pattern e.g. /api/v1/incidents/{incident_id} to regex
    regex_pattern = "^" + re.sub(r"\{[a-zA-Z0-9_]+\}", r"[a-zA-Z0-9_-]+", p_norm) + "$"
    return bool(re.match(regex_pattern, t_norm))


class TestScenarioValidator:
    """Validates that proposed scenarios strictly conform to actual implementation."""
    __test__ = False

    def __init__(self, inventory: FeatureInventory | None = None):
        self.inventory = inventory or discover_incidentflow_features()

    def validate_scenario(self, scenario: ProposedTestScenario) -> tuple[bool, str]:
        """
        Validate a proposed scenario.
        Returns (True, "") if valid, or (False, reason) if rejected.
        """
        # 1. Non-empty fields
        if not scenario.test_name or not scenario.test_name.strip():
            return False, "Test scenario has empty test_name"
        if not scenario.test_objective or not scenario.test_objective.strip():
            return False, "Test scenario has empty test_objective"
        if not scenario.expected_behavior or not scenario.expected_behavior.strip():
            return False, "Test scenario has empty expected_behavior"

        # 2. Check category
        if scenario.category not in self.inventory.known_categories:
            # Tolerant match on category case
            matched_cat = next(
                (c for c in self.inventory.known_categories if c.lower() == scenario.category.lower()),
                None,
            )
            if not matched_cat:
                return False, f"Unknown category '{scenario.category}'. Known: {self.inventory.known_categories}"

        # 3. Find matching endpoint in inventory
        method = scenario.http_method.strip().upper()
        target_path = scenario.target_endpoint.strip()

        matched_endpoint = None
        for feature in self.inventory.features.values():
            for ep in feature.endpoints:
                if ep.method.upper() == method and _match_route(ep.path, target_path):
                    matched_endpoint = ep
                    break
            if matched_endpoint:
                break

        if not matched_endpoint:
            return (
                False,
                f"No implemented endpoint matches [{method}] {target_path}. "
                "Rejecting unverified or fabricated route.",
            )

        # 4. Check expected status code
        if scenario.expected_status_code not in matched_endpoint.expected_status_codes:
            # Allow common HTTP error codes (401, 422) if method accepts body/auth
            allowable = set(matched_endpoint.expected_status_codes) | {401, 422}
            if scenario.expected_status_code not in allowable:
                return (
                    False,
                    f"Unexpected status code {scenario.expected_status_code} for [{method}] {target_path}. "
                    f"Expected one of: {matched_endpoint.expected_status_codes}",
                )

        return True, ""

    def filter_valid_scenarios(
        self,
        scenarios: list[ProposedTestScenario],
    ) -> tuple[list[ProposedTestScenario], list[tuple[ProposedTestScenario, str]]]:
        """
        Filter a list of scenarios into valid and rejected lists with reasons.
        """
        valid: list[ProposedTestScenario] = []
        rejected: list[tuple[ProposedTestScenario, str]] = []

        for sc in scenarios:
            is_valid, reason = self.validate_scenario(sc)
            if is_valid:
                valid.append(sc)
            else:
                rejected.append((sc, reason))

        return valid, rejected
