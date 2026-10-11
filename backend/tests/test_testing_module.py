"""Comprehensive test suite for the Automated Testing Module.

Covers:
1. Feature discovery accuracy & exclusion of nonexistent features.
2. Test-case schema validation & rejection of invalid/dangerous tests.
3. Test execution engine classification & isolated execution.
4. Data isolation: guarantees production database records remain untouched.
5. Testing API route security, authentication enforcement, and response schemas.
6. Test run history persistence and detailed reporting.
"""

import sys
import unittest
from pathlib import Path
from uuid import uuid4

import httpx

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.security import create_access_token
from app.db.session import async_session_factory, engine
from app.main import app
from app.models.models import Incident, User
from app.testing.feature_discovery import discover_features
from app.testing.schemas import TestCaseDefinition
from app.testing.test_case_generator import (
    compute_test_fingerprint,
    generate_and_validate_suite,
    generate_incidentflow_tests,
    select_round_robin_batch,
)
from app.testing.test_executor import executor_instance, test_session_factory, test_engine
from app.testing.test_validation import (
    ValidationError,
    validate_test_case,
    validate_test_suite,
)


class TestFeatureDiscovery(unittest.TestCase):
    """Verify feature discovery accuracy and exclusion of nonexistent features."""

    def test_feature_discovery_accuracy(self):
        inventory = discover_features()
        self.assertGreaterEqual(inventory.total_features, 12)
        feature_names = {f.name for f in inventory.features}

        # Must include all genuinely implemented features
        expected_features = {
            "Department Directory",
            "User Registration & Authentication",
            "Incident Creation & Lifecycle Management",
            "Incident Visibility & Role-Based Access Control",
            "Incident Status Transitions & Finite State Machine",
            "Optimistic Concurrency Control (OCC)",
            "Severity Level Assessment & Upgrades",
            "Incident Roster & Participant Roles",
            "Incident War Room Messaging",
            "Deterministic Audit Event Stream",
            "Real-Time WebSocket Gateway",
            "System Health & Diagnostics",
        }
        for ef in expected_features:
            self.assertIn(ef, feature_names, f"Feature '{ef}' should be discovered")

    def test_exclusion_of_unsupported_features(self):
        inventory = discover_features()
        feature_names = {f.name.lower() for f in inventory.features}

        # Must NOT include hypothetical / nonexistent features
        unsupported = ["email", "payment", "billing", "dependency mapping", "stripe", "slack integration"]
        for un in unsupported:
            for fn in feature_names:
                self.assertNotIn(un, fn, f"Hypothetical feature '{un}' should not be in discovered features")

        # Must explicitly record excluded features with reasons
        excluded_names = {ex["name"].lower() for ex in inventory.excluded_features}
        self.assertTrue(any("email" in en for en in excluded_names))
        self.assertTrue(any("billing" in en or "payment" in en for en in excluded_names))
        self.assertTrue(any("dependency" in en for en in excluded_names))


class TestTestCaseValidation(unittest.TestCase):
    """Verify test-case schema validation and security rule enforcement."""

    def setUp(self):
        self.inventory = discover_features()
        self.verified_names = {f.name for f in self.inventory.features}

    def test_valid_suite_generation_and_validation(self):
        approved_tests, errors = generate_and_validate_suite()
        self.assertGreaterEqual(len(approved_tests), 25)
        self.assertEqual(len(errors), 0, f"Expected 0 validation errors, got: {errors}")

    def test_reject_unverified_feature(self):
        invalid_tc = TestCaseDefinition(
            id="TC-FAKE-001",
            test_key="fake_test",
            feature_name="Nonexistent Email Dispatcher",
            category="FUNCTIONAL",
            title="Fake Email Notification Test",
            source_evidence={"endpoint": "/api/v1/fake", "method": "POST"},
            test_steps=["Step 1"],
            expected_outcome={"status_code": 200},
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_test_case(invalid_tc, self.verified_names)
        self.assertIn("references unverified feature", str(ctx.exception))

    def test_reject_dangerous_command_injection(self):
        dangerous_tc = TestCaseDefinition(
            id="TC-DANGEROUS-001",
            test_key="danger_test",
            feature_name="Department Directory",
            category="FUNCTIONAL",
            title="Malicious Input Test",
            source_evidence={"endpoint": "/api/v1/auth/departments", "method": "GET"},
            test_steps=["Step 1: DROP TABLE users CASCADE"],
            expected_outcome={"status_code": 200},
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_test_case(dangerous_tc, self.verified_names)
        self.assertIn("Disallowed dangerous pattern", str(ctx.exception))

    def test_reject_missing_status_code_or_close_code(self):
        incomplete_tc = TestCaseDefinition(
            id="TC-INC-001",
            test_key="inc_test",
            feature_name="Department Directory",
            category="FUNCTIONAL",
            title="Incomplete Test",
            source_evidence={"endpoint": "/api/v1/auth/departments", "method": "GET"},
            test_steps=["Step 1"],
            expected_outcome={"message": "hello"},  # No status_code
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_test_case(incomplete_tc, self.verified_names)
        self.assertIn("must specify an expected status_code", str(ctx.exception))


class TestExecutionEngineAndIsolation(unittest.IsolatedAsyncioTestCase):
    """Verify test execution, classification, and strict database isolation."""

    async def test_database_isolation_leaves_production_untouched(self):
        """Verify that running tests in the isolated test database does not mutate production data."""
        # Check initial production user count
        async with async_session_factory() as prod_db:
            from sqlalchemy import func, select
            prod_users_count_before = (await prod_db.execute(select(func.count(User.id)))).scalar_one()
            prod_incidents_count_before = (await prod_db.execute(select(func.count(Incident.id)))).scalar_one()

        # Execute tests via test executor
        tests, _ = generate_and_validate_suite()
        # Run a subset of tests to verify isolation
        sample_tests = tests[:5]

        async with async_session_factory() as prod_db:
            from app.testing.models import RunStatus, TestRunRecord
            run_rec = TestRunRecord(
                status=RunStatus.PENDING.value,
                generator_version="1.0.0",
                triggered_by="isolation_verifier@test.dev",
                total_tests=len(sample_tests),
            )
            prod_db.add(run_rec)
            await prod_db.commit()
            await prod_db.refresh(run_rec)

            completed = await executor_instance.execute_run(run_rec.id, sample_tests, prod_db)
            self.assertEqual(completed.status, RunStatus.COMPLETED.value)

        # Re-check production tables
        async with async_session_factory() as prod_db:
            prod_users_count_after = (await prod_db.execute(select(func.count(User.id)))).scalar_one()
            prod_incidents_count_after = (await prod_db.execute(select(func.count(Incident.id)))).scalar_one()

        # Production database must remain 100% untouched!
        self.assertEqual(
            prod_users_count_before,
            prod_users_count_after,
            "Production user count must not change during test execution!",
        )
        self.assertEqual(
            prod_incidents_count_before,
            prod_incidents_count_after,
            "Production incident count must not change during test execution!",
        )

    async def asyncTearDown(self):
        await engine.dispose()
        await test_engine.dispose()


class TestTestingAPIRoutes(unittest.IsolatedAsyncioTestCase):
    """Verify FastAPI testing API endpoints, authentication, and responses."""

    async def test_features_discovery_endpoint(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/v1/testing/features")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("features", data)
            self.assertIn("excluded_features", data)
            self.assertGreaterEqual(data["total_features"], 12)

    async def test_cases_listing_endpoint(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Default returns exactly 5 test cases for the active batch
            resp = await client.get("/api/v1/testing/cases")
            self.assertEqual(resp.status_code, 200)
            cases = resp.json()
            self.assertIsInstance(cases, list)
            self.assertEqual(len(cases), 5)

            # Query with all=true returns the full verified catalogue
            resp_all = await client.get("/api/v1/testing/cases?all=true")
            self.assertEqual(resp_all.status_code, 200)
            all_cases = resp_all.json()
            self.assertGreaterEqual(len(all_cases), 25)

    async def test_run_endpoint_requires_authentication(self):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Without Authorization header -> must be rejected
            resp = await client.post("/api/v1/testing/run", json={})
            self.assertIn(resp.status_code, [401, 403])

    async def test_authenticated_run_and_reporting_end_to_end(self):
        """Verify that an authenticated user can trigger a test run and inspect the report."""
        # Obtain user id from DB
        async with async_session_factory() as db:
            from sqlalchemy import select
            user = (await db.execute(select(User).limit(1))).scalar_one_or_none()
            if not user:
                self.skipTest("No users in DB for token creation")
            token = create_access_token(user.id, user.email)

        transport = httpx.ASGITransport(app=app)
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Trigger live test execution
            run_resp = await client.post("/api/v1/testing/run", json={}, headers=headers)
            self.assertEqual(run_resp.status_code, 200)
            data = run_resp.json()
            self.assertIn("run", data)
            self.assertIn("results", data)
            self.assertIn("feature_summaries", data)
            self.assertGreater(data["run"]["total_tests"], 0)
            self.assertEqual(data["run"]["status"], "COMPLETED")
            run_id = data["run"]["id"]

            # 2. Check runs list
            list_resp = await client.get("/api/v1/testing/runs", headers=headers)
            self.assertEqual(list_resp.status_code, 200)
            runs = list_resp.json()
            self.assertTrue(any(r["id"] == run_id for r in runs))

            # 3. Check detailed report retrieval
            detail_resp = await client.get(f"/api/v1/testing/runs/{run_id}", headers=headers)
            self.assertEqual(detail_resp.status_code, 200)
            detail = detail_resp.json()
            self.assertEqual(detail["run"]["id"], run_id)
            self.assertGreater(len(detail["results"]), 0)

    async def asyncTearDown(self):
        await engine.dispose()
        await test_engine.dispose()



class TestBatchGenerationAndRoundRobin(unittest.TestCase):
    """Verify 5-test batch generation, round-robin diversity, and cycle restart behavior."""

    def setUp(self):
        self.catalogue, _ = generate_and_validate_suite()

    def test_batch_generation_generates_exactly_5_cases(self):
        """Verify each generated batch has exactly 5 valid test cases."""
        batch_tests, batch_num, round_num, cycle_restarted, updated_history, msg = select_round_robin_batch(
            self.catalogue, history_fingerprints=[], batch_size=5, last_batch_number=0, last_round_number=1
        )
        self.assertEqual(len(batch_tests), 5)
        self.assertEqual(batch_num, 1)
        self.assertEqual(round_num, 1)
        self.assertFalse(cycle_restarted)
        self.assertEqual(len(updated_history), 5)
        # All 5 IDs and fingerprints must be distinct
        ids = [t.id for t in batch_tests]
        self.assertEqual(len(ids), len(set(ids)))

    def test_round_robin_different_cases_across_batches(self):
        """Verify consecutive batches select different test cases without duplicates."""
        b1, _, _, _, h1, _ = select_round_robin_batch(
            self.catalogue, history_fingerprints=[], batch_size=5, last_batch_number=0, last_round_number=1
        )
        b2, _, _, _, h2, _ = select_round_robin_batch(
            self.catalogue, history_fingerprints=h1, batch_size=5, last_batch_number=1, last_round_number=1
        )
        self.assertEqual(len(b1), 5)
        self.assertEqual(len(b2), 5)
        b1_ids = {t.id for t in b1}
        b2_ids = {t.id for t in b2}
        self.assertTrue(b1_ids.isdisjoint(b2_ids), "Batch 1 and Batch 2 must have no overlapping tests")

    def test_cycle_restart_after_catalogue_exhaustion(self):
        """Verify cycle restart when all catalogue scenarios are exhausted."""
        history = []
        last_batch = 0
        round_num = 1
        # Run through 6 batches (30 tests)
        for i in range(6):
            batch, last_batch, round_num, cycle_restarted, history, _ = select_round_robin_batch(
                self.catalogue, history_fingerprints=history, batch_size=5, last_batch_number=last_batch, last_round_number=round_num
            )
            self.assertEqual(len(batch), 5)
            self.assertFalse(cycle_restarted)

        self.assertEqual(len(history), 30)

        # 7th click should restart cycle
        batch7, batch_num7, round_num7, cycle_restarted7, history7, msg7 = select_round_robin_batch(
            self.catalogue, history_fingerprints=history, batch_size=5, last_batch_number=last_batch, last_round_number=round_num
        )
        self.assertTrue(cycle_restarted7)
        self.assertEqual(round_num7, 2)
        self.assertEqual(batch_num7, 1)
        self.assertEqual(len(batch7), 5)
        self.assertIn("Restarting cycle", msg7)

    def test_duplicate_rejection_within_batch(self):
        """Verify no duplicate scenarios or fingerprints occur within any batch."""
        history = []
        last_batch = 0
        round_num = 1
        for i in range(6):
            batch, last_batch, round_num, _, history, _ = select_round_robin_batch(
                self.catalogue, history_fingerprints=history, batch_size=5, last_batch_number=last_batch, last_round_number=round_num
            )
            ids = [t.id for t in batch]
            fps = [compute_test_fingerprint(t) for t in batch]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(len(fps), len(set(fps)))


if __name__ == "__main__":
    unittest.main()
