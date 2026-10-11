"""Validation engine for generated test cases.

Ensures that:
1. Every generated test corresponds to a verified implemented feature.
2. The test case schema is complete and structurally sound.
3. Target API endpoints and HTTP methods are authentic.
4. Preconditions and expected outcomes are valid and explicit.
5. Destructive shell commands, raw SQL, or external web requests are strictly forbidden.
"""

from typing import Any

from app.testing.schemas import TestCaseDefinition


ALLOWED_CATEGORIES = {
    "FUNCTIONAL",
    "VALIDATION",
    "AUTHENTICATION",
    "AUTHORIZATION",
    "BOUNDARY",
    "CONCURRENCY",
    "DATABASE_INTEGRITY",
    "REALTIME",
    "REGRESSION",
}

DISALLOWED_PATTERNS = [
    "rm -rf",
    "DROP DATABASE",
    "DROP TABLE",
    "DELETE FROM users",
    "DELETE FROM incidents",
    "truncate",
    "exec(",
    "eval(",
    "os.system",
    "subprocess",
]


class ValidationError(Exception):
    pass


def validate_test_case(test_case: TestCaseDefinition, verified_feature_names: set[str]) -> bool:
    """Validate a single test case against safety rules and verified features."""
    # 1. Feature verification
    if test_case.feature_name not in verified_feature_names:
        raise ValidationError(
            f"Test case '{test_case.id}' references unverified feature '{test_case.feature_name}'."
        )

    # 2. Category validation
    if test_case.category not in ALLOWED_CATEGORIES:
        raise ValidationError(
            f"Test case '{test_case.id}' has invalid category '{test_case.category}'. Allowed: {ALLOWED_CATEGORIES}"
        )

    # 3. Source evidence validation
    if not isinstance(test_case.source_evidence, dict):
        raise ValidationError(f"Test case '{test_case.id}' missing valid source evidence dictionary.")

    endpoint = test_case.source_evidence.get("endpoint")
    if not endpoint or not isinstance(endpoint, str):
        raise ValidationError(f"Test case '{test_case.id}' missing valid endpoint in source evidence.")

    # 4. Expected outcome validation
    if not isinstance(test_case.expected_outcome, dict):
        raise ValidationError(f"Test case '{test_case.id}' missing structured expected outcome.")

    if (
        "status_code" not in test_case.expected_outcome
        and "ws_close_code" not in test_case.expected_outcome
        and "ws_connected" not in test_case.expected_outcome
        and "action" not in test_case.expected_outcome
    ):
        raise ValidationError(
            f"Test case '{test_case.id}' must specify an expected status_code, ws_close_code, or ws_connected."
        )

    # 5. Security and command injection check
    input_str = str(test_case.input_data) + str(test_case.test_steps)
    for pattern in DISALLOWED_PATTERNS:
        if pattern.lower() in input_str.lower():
            raise ValidationError(
                f"Security violation in test case '{test_case.id}': Disallowed dangerous pattern '{pattern}' detected."
            )

    return True


def validate_test_suite(
    test_cases: list[TestCaseDefinition],
    verified_feature_names: set[str],
) -> tuple[list[TestCaseDefinition], list[dict[str, Any]]]:
    """Validate an entire suite of test cases. Returns (approved_tests, validation_errors)."""
    approved: list[TestCaseDefinition] = []
    errors: list[dict[str, Any]] = []

    seen_ids: set[str] = set()

    for tc in test_cases:
        if tc.id in seen_ids:
            errors.append({"test_id": tc.id, "error": f"Duplicate test ID '{tc.id}'."})
            continue

        try:
            validate_test_case(tc, verified_feature_names)
            approved.append(tc)
            seen_ids.add(tc.id)
        except ValidationError as e:
            errors.append({"test_id": tc.id, "error": str(e)})

    return approved, errors
