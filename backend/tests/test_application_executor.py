import pytest
from app.services.application_executor import application_executor
from app.core.state_machine import ApplicationMode, ApplicationStatus

def test_executor_mode_evaluation():
    # Mode A: auto-apply enabled and in allowlist
    policy_auto = {
        "auto_apply_enabled": True,
        "approval_required": False,
        "allowed_sources": ["mock_ats"]
    }
    job_mock = {"adapter_key": "mock_ats"}
    mode = application_executor.evaluate_mode(job_mock, policy_auto)
    assert mode == ApplicationMode.MODE_A_AUTO

    # Mode B: approval required
    policy_approval = {
        "auto_apply_enabled": True,
        "approval_required": True,
        "allowed_sources": ["mock_ats"]
    }
    mode_b = application_executor.evaluate_mode(job_mock, policy_approval)
    assert mode_b == ApplicationMode.MODE_B_APPROVAL

    # Mode C: external catalog requires assisted application
    job_catalog = {"adapter_key": "local_catalog"}
    mode_c = application_executor.evaluate_mode(job_catalog, policy_auto)
    assert mode_c == ApplicationMode.MODE_C_ASSISTED

def test_executor_submission_mock_confirmation():
    job_dict = {
        "title": "Staff AI Benchmark Evaluator",
        "company_name": "Nexus Frontier AI (Sandbox)",
        "adapter_key": "mock_ats"
    }
    res = application_executor.submit_application(
        application_id=1,
        job_dict=job_dict,
        candidate_dict={},
        documents_dict={},
        mode=ApplicationMode.MODE_A_AUTO
    )
    assert res["status"] == ApplicationStatus.SUBMITTED_CONFIRMED
    assert res["evidence"] is not None
    assert res["evidence"]["confirmation_id"].startswith("CONF-")
    assert res["evidence"]["verified"] is True
