"""Local Ollama AI integration for grounded test case generation."""

import json
from typing import Any
import httpx
from pydantic import BaseModel, Field

from incidentflow_testkit.config import TestkitSettings, get_settings
from incidentflow_testkit.feature_discovery import FeatureInventory, get_sanitized_system_summary


class ProposedTestScenario(BaseModel):
    feature_name: str = Field(description="Name of the verified feature being tested")
    test_name: str = Field(description="Descriptive snake_case test name, e.g. test_occ_version_conflict")
    test_objective: str = Field(description="Clear test goal and verification purpose")
    target_endpoint: str = Field(description="Relative path of the target API endpoint")
    http_method: str = Field(description="HTTP method: GET, POST, PATCH, etc.")
    category: str = Field(description="One of the verified categories")
    test_steps: list[str] = Field(default_factory=list, description="Step-by-step procedure")
    input_data: dict[str, Any] = Field(default_factory=dict, description="Test payload or parameters")
    expected_status_code: int = Field(description="Expected HTTP status code, e.g. 200, 201, 401, 403, 409, 422")
    expected_behavior: str = Field(description="Expected behavior or assertion criteria")
    source_evidence: str = Field(description="Citation of backend route/service rule justifying test")


class AIGenerationResponse(BaseModel):
    scenarios: list[ProposedTestScenario] = Field(default_factory=list)


class OllamaConnectionError(Exception):
    """Raised when Ollama daemon is unreachable."""
    pass


class OllamaModelNotFoundError(Exception):
    """Raised when the requested model is not present in local Ollama."""
    pass


class AIGenerationError(Exception):
    """Raised when Ollama response cannot be parsed or generation fails."""
    pass


class OllamaClient:
    """HTTP client for local Ollama instance."""

    def __init__(self, settings: TestkitSettings | None = None):
        self.settings = settings or get_settings()

    async def check_availability(self) -> list[str]:
        """
        Verify Ollama is running and query installed models.
        Returns list of available model names.
        Raises OllamaConnectionError if unreachable.
        """
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise OllamaConnectionError(
                        f"Ollama server responded with HTTP {resp.status_code} at {url}."
                    )
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return models
        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Cannot connect to local Ollama daemon at {self.settings.ollama_base_url}.\n"
                f"Troubleshooting instructions:\n"
                f"  1. Ensure Ollama is installed (https://ollama.com).\n"
                f"  2. Start Ollama in Windows terminal: 'ollama serve' or run Ollama from the Start Menu.\n"
                f"  3. Verify availability by visiting: {self.settings.ollama_base_url}/api/tags"
            ) from e
        except Exception as e:
            raise OllamaConnectionError(f"Failed to communicate with Ollama: {e}") from e

    async def verify_model_installed(self, model_name: str | None = None) -> str:
        """
        Verify the requested model is downloaded in local Ollama.
        Raises OllamaModelNotFoundError if not installed.
        """
        target = (model_name or self.settings.ollama_model).strip()
        models = await self.check_availability()

        # Check exact or prefix match (e.g. 'llama3' matches 'llama3:latest')
        matched = None
        for m in models:
            if m == target or m.split(":")[0] == target.split(":")[0]:
                matched = m
                break

        if not matched:
            available_list = ", ".join(models) if models else "None (no models downloaded yet)"
            raise OllamaModelNotFoundError(
                f"Model '{target}' is not installed in local Ollama.\n"
                f"Available local models: {available_list}\n\n"
                f"To install this model, run in Windows terminal:\n"
                f"  ollama pull {target}\n"
                f"Or specify another installed model in .env via OLLAMA_MODEL=<name> or CLI '--model <name>'."
            )
        return matched

    async def generate_scenarios(
        self,
        inventory: FeatureInventory,
        recent_fingerprints: list[str] | None = None,
        model_name: str | None = None,
        count: int = 10,
    ) -> list[ProposedTestScenario]:
        """
        Prompt the local Ollama model to generate grounded test scenarios based on actual code.
        Never executes arbitrary code; requires structured JSON conforming to schema.
        """
        active_model = await self.verify_model_installed(model_name)
        system_summary = get_sanitized_system_summary(inventory)

        system_prompt = (
            "You are a rigorous, senior software testing architect for FastAPI & PostgreSQL applications. "
            "Your task is to generate realistic, executable test scenarios for the IncidentFlow platform.\n\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. Ground EVERY test case strictly in the provided verified features summary.\n"
            "2. NEVER invent non-existent endpoints, hypothetical HTTP methods, or unsupported response codes.\n"
            "3. Produce varied scenarios across features: positive happy-path, validation errors (422), "
            "permission rejections (401/403), conflict guards (409), and not-found lookups (404).\n"
            "4. Respond ONLY with valid JSON conforming to the requested schema.\n"
        )

        user_prompt = (
            f"Here is the verified implementation of IncidentFlow:\n\n"
            f"{system_summary}\n\n"
            f"Please propose up to {count} distinct, high-value test scenarios.\n"
            f"Return JSON strictly adhering to this structure:\n"
            f"{{\n"
            f'  "scenarios": [\n'
            f"    {{\n"
            f'      "feature_name": "Name of feature from summary",\n'
            f'      "test_name": "test_snake_case_name",\n'
            f'      "test_objective": "Specific goal of this test",\n'
            f'      "target_endpoint": "/api/v1/...",\n'
            f'      "http_method": "GET or POST or PATCH",\n'
            f'      "category": "Category from summary",\n'
            f'      "test_steps": ["Step 1", "Step 2"],\n'
            f'      "input_data": {{"key": "value"}},\n'
            f'      "expected_status_code": 200,\n'
            f'      "expected_behavior": "Assertion expectation",\n'
            f'      "source_evidence": "Reference from summary"\n'
            f"    }}\n"
            f"  ]\n"
            f"}}"
        )

        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.3,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=float(self.settings.ollama_timeout_seconds)) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    raise AIGenerationError(
                        f"Ollama generation failed with HTTP {resp.status_code}: {resp.text}"
                    )
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                if not content:
                    raise AIGenerationError("Ollama returned an empty response.")

                parsed_json = json.loads(content)
                # Parse into Pydantic model
                if "scenarios" not in parsed_json and isinstance(parsed_json, list):
                    parsed_json = {"scenarios": parsed_json}

                validated = AIGenerationResponse.model_validate(parsed_json)
                return validated.scenarios
        except json.JSONDecodeError as e:
            raise AIGenerationError(f"Ollama output was not valid JSON: {e}") from e
        except Exception as e:
            if isinstance(e, (OllamaConnectionError, OllamaModelNotFoundError, AIGenerationError)):
                raise
            raise AIGenerationError(f"Error during AI test generation: {e}") from e
