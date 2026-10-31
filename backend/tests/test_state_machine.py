import pytest
from app.core.state_machine import ApplicationStatus, ApplicationStateMachine

def test_valid_state_transitions():
    # DISCOVERED -> VERIFIED
    assert ApplicationStateMachine.can_transition(ApplicationStatus.DISCOVERED, ApplicationStatus.VERIFIED)
    # VERIFIED -> MATCHED
    assert ApplicationStateMachine.can_transition(ApplicationStatus.VERIFIED, ApplicationStatus.MATCHED)
    # MATCHED -> PREPARED
    assert ApplicationStateMachine.can_transition(ApplicationStatus.MATCHED, ApplicationStatus.PREPARED)
    # PREPARED -> AWAITING_APPROVAL
    assert ApplicationStateMachine.can_transition(ApplicationStatus.PREPARED, ApplicationStatus.AWAITING_APPROVAL)
    # AWAITING_APPROVAL -> SUBMITTING
    assert ApplicationStateMachine.can_transition(ApplicationStatus.AWAITING_APPROVAL, ApplicationStatus.SUBMITTING)
    # SUBMITTING -> SUBMITTED_CONFIRMED
    assert ApplicationStateMachine.can_transition(ApplicationStatus.SUBMITTING, ApplicationStatus.SUBMITTED_CONFIRMED)

def test_invalid_state_transitions():
    # Cannot jump from DISCOVERED directly to SUBMITTED_CONFIRMED
    assert not ApplicationStateMachine.can_transition(ApplicationStatus.DISCOVERED, ApplicationStatus.SUBMITTED_CONFIRMED)
    
    with pytest.raises(ValueError):
        ApplicationStateMachine.validate_transition(ApplicationStatus.DISCOVERED, ApplicationStatus.SUBMITTED_CONFIRMED)

    # Cannot jump from REJECTED to SUBMITTING
    assert not ApplicationStateMachine.can_transition(ApplicationStatus.REJECTED, ApplicationStatus.SUBMITTING)
