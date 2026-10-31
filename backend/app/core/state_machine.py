import enum
from typing import Dict, Set

class ApplicationStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    VERIFIED = "VERIFIED"
    MATCHED = "MATCHED"
    PREPARED = "PREPARED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    AUTHORIZED_AUTO_APPLY = "AUTHORIZED_AUTO_APPLY"
    SUBMITTING = "SUBMITTING"
    SUBMITTED_CONFIRMED = "SUBMITTED_CONFIRMED"
    SUBMISSION_UNCERTAIN = "SUBMISSION_UNCERTAIN"
    FAILED = "FAILED"
    UNDER_REVIEW = "UNDER_REVIEW"
    INTERVIEW = "INTERVIEW"
    OFFER = "OFFER"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

class ApplicationMode(str, enum.Enum):
    MODE_A_AUTO = "MODE_A_AUTO"
    MODE_B_APPROVAL = "MODE_B_APPROVAL"
    MODE_C_ASSISTED = "MODE_C_ASSISTED"

class ApplicationStateMachine:
    VALID_TRANSITIONS: Dict[ApplicationStatus, Set[ApplicationStatus]] = {
        ApplicationStatus.DISCOVERED: {
            ApplicationStatus.VERIFIED,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.VERIFIED: {
            ApplicationStatus.MATCHED,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.MATCHED: {
            ApplicationStatus.PREPARED,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.PREPARED: {
            ApplicationStatus.AWAITING_APPROVAL,
            ApplicationStatus.AUTHORIZED_AUTO_APPLY,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.AWAITING_APPROVAL: {
            ApplicationStatus.SUBMITTING,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.AUTHORIZED_AUTO_APPLY: {
            ApplicationStatus.SUBMITTING,
            ApplicationStatus.AWAITING_APPROVAL,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.SUBMITTING: {
            ApplicationStatus.SUBMITTED_CONFIRMED,
            ApplicationStatus.SUBMISSION_UNCERTAIN,
            ApplicationStatus.FAILED
        },
        ApplicationStatus.SUBMISSION_UNCERTAIN: {
            ApplicationStatus.SUBMITTED_CONFIRMED,
            ApplicationStatus.FAILED,
            ApplicationStatus.UNDER_REVIEW
        },
        ApplicationStatus.SUBMITTED_CONFIRMED: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.OFFER,
            ApplicationStatus.WITHDRAWN
        },
        ApplicationStatus.UNDER_REVIEW: {
            ApplicationStatus.INTERVIEW,
            ApplicationStatus.REJECTED,
            ApplicationStatus.OFFER,
            ApplicationStatus.WITHDRAWN
        },
        ApplicationStatus.INTERVIEW: {
            ApplicationStatus.OFFER,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN
        },
        ApplicationStatus.OFFER: {
            ApplicationStatus.WITHDRAWN
        },
        ApplicationStatus.FAILED: {
            ApplicationStatus.PREPARED,
            ApplicationStatus.AWAITING_APPROVAL
        },
        ApplicationStatus.REJECTED: set(),
        ApplicationStatus.WITHDRAWN: set()
    }

    @classmethod
    def can_transition(cls, current_status: ApplicationStatus, next_status: ApplicationStatus) -> bool:
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return next_status in allowed

    @classmethod
    def validate_transition(cls, current_status: ApplicationStatus, next_status: ApplicationStatus):
        if not cls.can_transition(current_status, next_status):
            raise ValueError(
                f"Invalid application state transition from '{current_status.value}' to '{next_status.value}'."
            )
