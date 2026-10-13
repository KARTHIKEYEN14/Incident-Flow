"""Command Line Interface for the IncidentFlow Testkit."""

import argparse
import asyncio
import sys

from incidentflow_testkit.ai_generator import (
    AIGenerationError,
    OllamaClient,
    OllamaConnectionError,
    OllamaModelNotFoundError,
)
from incidentflow_testkit.config import get_settings
from incidentflow_testkit.feature_discovery import discover_incidentflow_features
from incidentflow_testkit.report import display_latest_report, format_terminal_report
from incidentflow_testkit.test_catalogue import TestCatalogue
from incidentflow_testkit.test_executor import generate_pytest_files, run_latest_batch
from incidentflow_testkit.test_validator import TestScenarioValidator


async def cmd_check_ai(args) -> int:
    """Verify local Ollama daemon connection and installed models."""
    settings = get_settings()
    client = OllamaClient(settings)
    print(f"\n[AI Probe] Checking Ollama at {settings.ollama_base_url}...")
    try:
        models = await client.check_availability()
        print(f"[OK] Ollama is active! Found {len(models)} installed model(s):")
        for m in models:
            marker = " (configured default)" if m == settings.ollama_model or m.startswith(settings.ollama_model.split(":")[0]) else ""
            print(f"  - {m}{marker}")
        return 0
    except (OllamaConnectionError, OllamaModelNotFoundError) as e:
        print(f"\n[ERROR] {e}\n", file=sys.stderr)
        return 1


def cmd_features(args) -> int:
    """Display discovered features from the IncidentFlow codebase."""
    inventory = discover_incidentflow_features()
    print("\n" + "=" * 70)
    print(" INCIDENTFLOW - DISCOVERED VERIFIED FEATURES")
    print("=" * 70)
    for key, feat in inventory.features.items():
        print(f"\n[{feat.category}] {feat.name}")
        print(f"  Description: {feat.description}")
        for ep in feat.endpoints:
            auth = "Auth" if ep.auth_required else "Public"
            print(f"  - [{ep.method}] {ep.path} ({auth}) -> Status: {ep.expected_status_codes}")
    print("\n" + "=" * 70 + "\n")
    return 0


async def cmd_generate(args) -> int:
    """Generate up to 10 grounded test cases using local Ollama model."""
    settings = get_settings()
    limit = args.limit or settings.max_tests_per_batch
    model_name = args.model or settings.ollama_model

    print(f"\n[1/4] Inspecting IncidentFlow codebase for verified features...")
    inventory = discover_incidentflow_features(settings.backend_dir)
    print(f"      Discovered {len(inventory.features)} verified feature areas.")

    print(f"[2/4] Connecting to local Ollama (model: {model_name})...")
    client = OllamaClient(settings)
    try:
        active_model = await client.verify_model_installed(model_name)
    except (OllamaConnectionError, OllamaModelNotFoundError) as e:
        print(f"\n[AI Setup Error]\n{e}\n", file=sys.stderr)
        return 1

    print(f"[3/4] Requesting test scenarios from {active_model}...")
    try:
        candidates = await client.generate_scenarios(
            inventory=inventory,
            model_name=active_model,
            count=limit * 2,  # Request sufficient candidate pool
        )
        print(f"      Received {len(candidates)} raw proposed scenario(s).")
    except (OllamaConnectionError, OllamaModelNotFoundError, AIGenerationError) as e:
        print(f"\n[Generation Error] {e}\n", file=sys.stderr)
        return 1

    # Validate candidates against actual implementation
    print(f"[4/4] Validating and selecting distinct, novel scenarios...")
    validator = TestScenarioValidator(inventory)
    valid_scenarios, rejected = validator.filter_valid_scenarios(candidates)

    if rejected:
        print(f"      Filtered out {len(rejected)} scenario(s) not matching verified implementation.")

    if not valid_scenarios:
        print(
            "\n[!] The AI model proposed 0 valid scenarios matching verified endpoints.",
            file=sys.stderr,
        )
        return 1

    catalogue = TestCatalogue(settings)
    batch, note = catalogue.select_batch(valid_scenarios, model_name=active_model, limit=limit)

    test_file = generate_pytest_files(batch, settings)

    print("\n" + "=" * 70)
    print(" GENERATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"Batch ID:        {batch.batch_id}")
    print(f"Model Used:      {active_model}")
    print(f"Tests Generated: {len(batch.scenarios)} (limit: {limit})")
    print(f"Selection Note:  {note}")
    print(f"Test File:       {test_file}")
    print("-" * 70)
    for s in batch.scenarios:
        print(f"  [{s.scenario_id}] {s.scenario.test_name}")
        print(f"         Feature:   {s.scenario.feature_name} ({s.scenario.category})")
        print(f"         Target:    [{s.scenario.http_method}] {s.scenario.target_endpoint}")
        print(f"         Expected:  HTTP {s.scenario.expected_status_code}")
        print(f"         Fingerprint: {s.fingerprint}")
    print("=" * 70)
    print("\nTo execute this batch, run:")
    print("  python -m incidentflow_testkit.cli run\n")
    return 0


def cmd_run(args) -> int:
    """Execute the latest generated test batch with pytest."""
    settings = get_settings()
    print("\n[*] Executing latest generated test batch...")
    try:
        report, exit_code = run_latest_batch(verbose=args.verbose, settings=settings)
    except FileNotFoundError as e:
        print(f"\n[Error] {e}\n", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[Execution Error] {e}\n", file=sys.stderr)
        return 1

    # Display report
    print(format_terminal_report(report))
    return exit_code


def cmd_report(args) -> int:
    """Show the latest test execution report."""
    return display_latest_report()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="incidentflow-testkit",
        description="Standalone AI-Powered Testing Toolkit for IncidentFlow",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate fresh AI test cases")
    gen_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum test cases to generate (1 to 10, default: 5)",
    )
    gen_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Ollama model name (overrides OLLAMA_MODEL config)",
    )

    # run
    run_parser = subparsers.add_parser("run", help="Run the latest generated test batch")
    run_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose pytest output")

    # report
    subparsers.add_parser("report", help="Show the latest execution report")

    # features
    subparsers.add_parser("features", help="List discovered features from IncidentFlow codebase")

    # check-ai
    subparsers.add_parser("check-ai", help="Verify Ollama connection and model availability")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "generate":
        code = asyncio.run(cmd_generate(args))
    elif args.command == "run":
        code = cmd_run(args)
    elif args.command == "report":
        code = cmd_report(args)
    elif args.command == "features":
        code = cmd_features(args)
    elif args.command == "check-ai":
        code = asyncio.run(cmd_check_ai(args))
    else:
        parser.print_help()
        code = 1

    sys.exit(code)


if __name__ == "__main__":
    main()
