"""
Unit and Integration Tests for the Visibility & Operations Agent Loop
"""
import json
import os
import tempfile
import pytest

from src.agents.auditor_agent import AuditorAgent
from src.agents.strategist_agent import StrategistAgent
from src.agents.operator_agent import OperatorAgent
from src.orchestrator.pipeline import VisibilityPipeline


SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Acme AI Solutions</title>
</head>
<body>
    <h1>Enterprise AI Automation Platform</h1>
    <h2>What is Acme AI?</h2>
    <p>Acme AI is an intelligent orchestration platform designed to automate complex developer workflows and boost productivity by 40%.</p>
    <h2>Core Features</h2>
    <ul>
        <li>Automated agent loops</li>
        <li>Continuous code optimization</li>
    </ul>
</body>
</html>"""


def test_auditor_agent():
    auditor = AuditorAgent()
    report = auditor.run("test_target", raw_html=SAMPLE_HTML)

    assert report.target == "test_target"
    assert 0 <= report.scores.overall <= 100
    assert 0 <= report.scores.seo <= 100
    assert 0 <= report.scores.aeo <= 100
    assert 0 <= report.scores.geo <= 100
    assert 0 <= report.scores.aio <= 100

    # Should detect missing meta description
    missing_meta = [f for f in report.findings if f.name == "Missing Meta Description"]
    assert len(missing_meta) == 1

    # Should detect missing JSON-LD schema
    missing_schema = [f for f in report.findings if "JSON-LD" in f.name]
    assert len(missing_schema) >= 1


def test_strategist_agent():
    auditor = AuditorAgent()
    report = auditor.run("test_target", raw_html=SAMPLE_HTML)

    strategist = StrategistAgent()
    plan = strategist.run(report)

    assert plan.target == "test_target"
    assert len(plan.recommendations) >= 3
    assert plan.target_scores.overall > plan.current_scores.overall
    assert len(plan.keyword_opportunities) > 0
    assert "schema.org/FAQPage" in plan.schema_requirements


def test_operator_agent():
    auditor = AuditorAgent()
    report = auditor.run("test_target", raw_html=SAMPLE_HTML)
    strategist = StrategistAgent()
    plan = strategist.run(report)

    operator = OperatorAgent()
    result = operator.run(plan, site_name="Acme AI")

    assert len(result.artifacts) >= 5
    assert len(result.task_checklist) >= 4

    # Verify JSON-LD artifact is valid JSON
    json_ld_artifact = result.get_artifact_by_type("json_ld")
    assert json_ld_artifact is not None
    parsed_json = json.loads(json_ld_artifact.content)
    assert "@context" in parsed_json
    assert "@graph" in parsed_json

    # Verify llms.txt artifact
    llms_artifact = result.get_artifact_by_type("llms_txt")
    assert llms_artifact is not None
    assert "# Acme AI" in llms_artifact.content

    # Verify FAQ HTML artifact
    faq_artifact = result.get_artifact_by_type("faq_html")
    assert faq_artifact is not None
    assert "schema.org/Question" in faq_artifact.content


def test_end_to_end_pipeline_loop():
    with tempfile.TemporaryDirectory() as tmpdir:
        pipeline = VisibilityPipeline()
        result = pipeline.run_loop(
            target="Acme Test Site",
            raw_html=SAMPLE_HTML,
            output_dir=tmpdir,
            perform_loopback=True,
        )

        assert result.initial_audit is not None
        assert result.action_plan is not None
        assert result.operation_result is not None
        assert result.re_audit is not None
        assert result.score_delta is not None

        # Closed-loop verification: score should improve!
        assert result.re_audit.scores.overall > result.initial_audit.scores.overall
        assert result.score_delta["overall"] > 0

        # Check exported files
        assert os.path.exists(os.path.join(tmpdir, "audit_report.json"))
        assert os.path.exists(os.path.join(tmpdir, "action_plan.json"))
        assert os.path.exists(os.path.join(tmpdir, "schema.jsonld"))
        assert os.path.exists(os.path.join(tmpdir, "llms.txt"))
        assert os.path.exists(os.path.join(tmpdir, "faq_section.html"))
        assert os.path.exists(os.path.join(tmpdir, "operations_summary.md"))
        assert os.path.exists(os.path.join(tmpdir, "optimized_site.html"))
