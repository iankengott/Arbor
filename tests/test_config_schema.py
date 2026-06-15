from __future__ import annotations

import pytest

from arbor.core.config import AgentConfig
from arbor.core.config_schema import redact_secrets, redacted_snapshot


def test_agent_config_routes_flat_keys_into_nested_groups() -> None:
    cfg = AgentConfig(
        provider="openai-responses",
        model="gpt-4.1",
        api_key="secret",
        bash_timeout_default=42,
        context_window=12_345,
    )

    assert cfg.llm.provider == "openai-responses"
    assert cfg.provider == "openai-responses"
    assert cfg.llm.model == "gpt-4.1"
    assert cfg.timeout.bash_default == 42
    assert cfg.bash_timeout_default == 42
    assert cfg.context.window == 12_345
    assert cfg.context_window == 12_345


def test_agent_config_flat_assignment_and_model_copy_stay_in_sync() -> None:
    cfg = AgentConfig()

    cfg.provider = "litellm"
    copied = cfg.model_copy(update={"bash_timeout_default": 99, "context_window": 500})

    assert cfg.llm.provider == "litellm"
    assert copied.timeout.bash_default == 99
    assert copied.bash_timeout_default == 99
    assert copied.context.window == 500


def test_redacted_snapshot_masks_secret_values_and_url_credentials() -> None:
    cfg = AgentConfig(
        api_key="sk-test",
        base_url="https://user:pass@example.com/v1",
    )

    snapshot = redacted_snapshot(cfg)

    assert snapshot["llm"]["api_key"] == "***REDACTED***"
    assert snapshot["llm"]["base_url"] == "https://***@example.com/v1"


def test_redact_secrets_recurses_through_nested_data() -> None:
    assert redact_secrets({"outer": [{"api_key": "secret"}]}) == {
        "outer": [{"api_key": "***REDACTED***"}]
    }


def test_invalid_interaction_mode_is_rejected() -> None:
    from arbor.core.config_schema import UIConfig

    with pytest.raises(ValueError, match="interaction_mode"):
        UIConfig(interaction_mode="manual")
