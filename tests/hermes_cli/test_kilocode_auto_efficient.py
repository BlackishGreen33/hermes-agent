"""Regression coverage for Kilo Auto Efficient model discovery."""

import os
from unittest.mock import patch

import pytest

from hermes_cli.model_normalize import normalize_model_for_provider
from hermes_cli.model_switch import list_authenticated_providers
import hermes_cli.models as _models_mod
from hermes_cli.models import provider_model_ids
from hermes_cli.models_validate import validate_requested_model


@pytest.mark.parametrize(
    "models_dev_models",
    [[], ["anthropic/claude-sonnet-4.6"]],
)
def test_kilocode_catalog_keeps_auto_efficient(models_dev_models):
    """Curated provider entries survive a models.dev response that omits them."""
    curated = list(_models_mod._PROVIDER_MODELS["kilocode"])
    with (
        patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            return_value={"api_key": "", "base_url": "https://api.kilo.ai/api/gateway"},
        ),
        patch(
            "agent.models_dev.list_agentic_models",
            return_value=models_dev_models,
        ),
    ):
        models = provider_model_ids("kilocode")

    assert set(curated).issubset(models)


def test_kilocode_picker_includes_auto_efficient():
    """Authenticated Kilo users can discover every curated entry in the picker."""
    curated = list(_models_mod._PROVIDER_MODELS["kilocode"])
    with (
        patch.dict(os.environ, {"KILOCODE_API_KEY": "test-key"}, clear=True),
        patch(
            "agent.models_dev.fetch_models_dev",
            return_value={"kilo": {"env": ["KILOCODE_API_KEY"]}},
        ),
        patch(
            "agent.models_dev.list_agentic_models",
            return_value=["anthropic/claude-sonnet-4.6"],
        ),
        patch(
            "hermes_cli.auth.resolve_api_key_provider_credentials",
            return_value={"api_key": "", "base_url": "https://api.kilo.ai/api/gateway"},
        ),
        patch("hermes_cli.models.get_curated_nous_model_ids", return_value=[]),
        patch(
            "hermes_cli.models.cached_provider_model_ids",
            side_effect=lambda provider, **_kwargs: provider_model_ids(provider),
        ),
    ):
        rows = list_authenticated_providers(
            current_provider="kilocode",
            max_models=None,
        )

    kilo = next(row for row in rows if row["slug"] == "kilocode")
    assert set(curated).issubset(kilo["models"])


def test_kilocode_auto_efficient_is_valid_and_preserved():
    """Validation preserves a curated provider model ID."""
    requested = _models_mod._PROVIDER_MODELS["kilocode"][0]
    normalized = normalize_model_for_provider(requested, "kilocode")

    with patch(
        "hermes_cli.models.fetch_api_models",
        return_value=["anthropic/claude-sonnet-4.6"],
    ):
        result = validate_requested_model(normalized, "kilocode")

    assert normalized == requested
    assert result["accepted"] is True
    assert result["persist"] is True
    assert result["recognized"] is True
    assert "corrected_model" not in result
