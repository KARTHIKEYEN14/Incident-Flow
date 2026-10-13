"""Unit tests for Ollama client and AI generation response parsing."""

import json
import pytest
import httpx
from incidentflow_testkit.ai_generator import (
    AIGenerationError,
    OllamaClient,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    ProposedTestScenario,
)
from incidentflow_testkit.config import TestkitSettings
from incidentflow_testkit.feature_discovery import discover_incidentflow_features


@pytest.mark.asyncio
async def test_ollama_availability_success(monkeypatch):
    """Test successful response parsing from /api/tags."""
    settings = TestkitSettings(ollama_base_url="http://mock-ollama:11434")
    client = OllamaClient(settings)

    class MockResponse:
        status_code = 200
        def json(self):
            return {"models": [{"name": "llama3:latest"}, {"name": "mistral:latest"}]}

    async def mock_get(self, url, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    models = await client.check_availability()
    assert "llama3:latest" in models
    assert "mistral:latest" in models


@pytest.mark.asyncio
async def test_ollama_unreachable_raises_error(monkeypatch):
    """Test clear error output when Ollama daemon is unreachable."""
    settings = TestkitSettings(ollama_base_url="http://invalid-host:11434")
    client = OllamaClient(settings)

    async def mock_get(self, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(OllamaConnectionError, match="Cannot connect to local Ollama daemon"):
        await client.check_availability()


@pytest.mark.asyncio
async def test_ollama_model_not_found_raises_error(monkeypatch):
    """Test error when model is not downloaded in Ollama."""
    settings = TestkitSettings(ollama_model="nonexistent-model:latest")
    client = OllamaClient(settings)

    class MockResponse:
        status_code = 200
        def json(self):
            return {"models": [{"name": "llama3:latest"}]}

    async def mock_get(self, url, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    with pytest.raises(OllamaModelNotFoundError, match="ollama pull"):
        await client.verify_model_installed("nonexistent-model:latest")


@pytest.mark.asyncio
async def test_structured_ai_response_parsing(monkeypatch):
    """Test parsing structured JSON scenario list from Ollama."""
    settings = TestkitSettings(ollama_model="llama3:latest")
    client = OllamaClient(settings)

    async def mock_verify(m=None):
        return "llama3:latest"

    monkeypatch.setattr(client, "verify_model_installed", mock_verify)

    raw_ai_payload = {
        "message": {
            "content": json.dumps({
                "scenarios": [
                    {
                        "feature_name": "System Health Check",
                        "test_name": "test_health_probe",
                        "test_objective": "Verify health endpoint",
                        "target_endpoint": "/health",
                        "http_method": "GET",
                        "category": "SystemHealth",
                        "test_steps": ["Send GET /health"],
                        "input_data": {},
                        "expected_status_code": 200,
                        "expected_behavior": "Status ok",
                        "source_evidence": "main.py health check",
                    }
                ]
            })
        }
    }

    class MockPostResponse:
        status_code = 200
        def json(self):
            return raw_ai_payload

    async def mock_post(self, url, **kwargs):
        return MockPostResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    inventory = discover_incidentflow_features()
    scenarios = await client.generate_scenarios(inventory, model_name="llama3:latest")
    assert len(scenarios) == 1
    assert scenarios[0].test_name == "test_health_probe"
    assert scenarios[0].expected_status_code == 200


@pytest.mark.asyncio
async def test_malformed_ai_response_handling(monkeypatch):
    """Test handling when model returns non-JSON text."""
    settings = TestkitSettings(ollama_model="llama3:latest")
    client = OllamaClient(settings)
    async def mock_verify(m=None):
        return "llama3:latest"
    monkeypatch.setattr(client, "verify_model_installed", mock_verify)

    class MockPostResponse:
        status_code = 200
        def json(self):
            return {"message": {"content": "I am not JSON, here are some tests:"}}

    async def mock_post(self, url, **kwargs):
        return MockPostResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    inventory = discover_incidentflow_features()
    with pytest.raises(AIGenerationError, match="not valid JSON"):
        await client.generate_scenarios(inventory)
