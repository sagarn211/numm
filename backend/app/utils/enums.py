from enum import Enum

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    CPSE_OFFICER = "CPSE_OFFICER"
    REVIEWER = "REVIEWER"

class MatchClassification(str, Enum):
    EXACT = "EXACT"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    FUNCTIONAL_EQUIVALENT = "FUNCTIONAL_EQUIVALENT"
    NO_MATCH = "NO_MATCH"
