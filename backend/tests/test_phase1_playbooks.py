"""Golden contracts for Phase 1; critical outputs never depend on AI."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


@pytest.mark.parametrize("scenario", json.loads((Path(__file__).parent / "fixtures/scenarios.yaml").read_text())["phase1_playbooks"])
def test_R1_golden_facts_version_actions(scenario, monkeypatch):
    from app.domain.facts import FACTS_ADAPTER
    from app.domain.playbooks import evaluate
    from app.domain.sources import SOURCES
    import app.services.evidence_extraction as extraction
    monkeypatch.setattr(extraction, "extract_evidence", lambda **kwargs: pytest.fail("AI/extraction called for actions"))
    facts = FACTS_ADAPTER.validate_python(scenario["facts"])
    plan = evaluate(facts, as_of=NOW)
    assert [a.id for a in plan.actions] == scenario["action_ids"]
    assert plan == evaluate(facts, as_of=NOW, version=plan.playbook_version)
    assert plan.fact_schema_version == "1.0"
    assert not any("recover" in name for name in plan.model_fields)
    assert all(a.official_source_id in SOURCES for a in plan.actions if a.official_source_id)
    assert [a.order for a in plan.actions] == list(range(1, len(plan.actions) + 1))


def test_R1_unknown_is_not_false_and_discriminator_is_strict():
    from app.domain.facts import FACTS_ADAPTER
    facts = FACTS_ADAPTER.validate_python({"kind": "financial_authorization_unknown"})
    assert facts.authorization == "unknown"
    assert facts.remote_access is None and facts.amount is None
    assert facts.transaction_id is None and facts.account_compromised is None
    with pytest.raises(ValidationError):
        FACTS_ADAPTER.validate_python({"kind": "financial_scam_transfer", "authorization": "unauthorized"})
    with pytest.raises(ValidationError):
        FACTS_ADAPTER.validate_python({"kind": "financial_authorization_unknown", "remote_access": "false"})
    with pytest.raises(ValidationError):
        FACTS_ADAPTER.validate_python({"kind": "financial_scam_transfer", "critical_action": "refund"})


def test_R1_reporting_fields_do_not_gate_actions_or_question_priority():
    from app.domain.facts import FACTS_ADAPTER
    from app.domain.playbooks import evaluate, next_unanswered_fact
    minimal = FACTS_ADAPTER.validate_python({"kind": "financial_scam_transfer"})
    detailed = minimal.model_copy(update={"amount": 2500, "transaction_id": "SYNTH-123"})
    assert [a.id for a in evaluate(minimal, as_of=NOW).actions] == [a.id for a in evaluate(detailed, as_of=NOW).actions]
    unknown = FACTS_ADAPTER.validate_python({"kind": "financial_authorization_unknown"})
    assert next_unanswered_fact(unknown).field == "authorization"
    assert next_unanswered_fact(minimal).field not in {"amount", "transaction_id"}


def test_R1_engine_has_no_provider_or_network_imports():
    import ast
    from app.domain import playbooks
    source = ast.parse(Path(playbooks.__file__).read_text())
    imports = [n.module or "" for n in ast.walk(source) if isinstance(n, ast.ImportFrom)]
    imports += [alias.name for n in ast.walk(source) if isinstance(n, ast.Import) for alias in n.names]
    assert not any(any(bad in name for bad in ("anthropic", "gemini", "httpx", "requests", "evidence_extraction")) for name in imports)


def test_R1_unverified_ai_inferences_cannot_select_critical_actions():
    from app.domain.facts import FACTS_ADAPTER
    with pytest.raises(ValidationError):
        FACTS_ADAPTER.validate_python({"kind": "financial_scam_transfer", "provenance": [
            {"field": "authorization", "origin": "inference", "verified": False}]})
    facts = FACTS_ADAPTER.validate_python({"kind": "financial_authorization_unknown", "provenance": [
        {"field": "authorization", "origin": "inference", "verified": False}]})
    assert facts.authorization == "unknown"
