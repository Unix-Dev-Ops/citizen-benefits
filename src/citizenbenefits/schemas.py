from datetime import UTC, date, datetime
from enum import Enum
import re
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator

class CitizenshipStatus(str, Enum):
    US_CITIZEN = "us_citizen"
    US_NATIONAL = "us_national"
    LAWFUL_PERMANENT_RESIDENT = "lawful_permanent_resident"
    COFA_CITIZEN = "cofa_citizen"
    VETERAN_OR_MILITARY = "veteran_or_military"
    OTHER_NOT_LISTED = "other_not_listed"

class IncomeBand(str, Enum):
    UNDER_50_FPL = "under_50_fpl"
    FPL_50_100 = "50_100_fpl"
    FPL_100_130 = "100_130_fpl"
    FPL_130_200 = "130_200_fpl"
    OVER_200_FPL = "over_200_fpl"

class EarnedIncomeShare(str, Enum):
    NONE = "none"
    SOME = "some"
    MOST = "most"
    ALL = "all"

class AgeBand(str, Enum):
    UNDER_18 = "under_18"
    AGE_18_59 = "18_59"
    AGE_60_64 = "60_64"
    AGE_65_PLUS = "65_plus"

class EligibilityRequest(BaseModel):
    status: CitizenshipStatus = Field(description="Immigration or citizenship status")
    state: str = Field(description="2-letter US state code")
    zip: str | None = Field(default=None, description="Optional 5-digit US ZIP code")
    household_size: int = Field(description="Total number of members in household")
    total_income_band: IncomeBand = Field(description="FPL-relative household total income band")
    earned_income_share: EarnedIncomeShare = Field(description="Share of total income that is earned")
    age_band: AgeBand = Field(description="Age category of the primary applicant")
    has_disability: bool = Field(description="Whether any household member has a disability")
    is_pregnant: bool = Field(description="Whether any household member is pregnant")
    num_children: int = Field(description="Number of children under 18 in the household")
    is_married: bool = Field(description="Marriage status (filing status)")
    is_veteran_or_military: bool = Field(description="Whether any member is a veteran or active military")

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not re.match(r"^[A-Z]{2}$", cleaned):
            raise ValueError("State must be a 2-letter postal abbreviation (e.g., OH).")
        return cleaned

    @field_validator("zip")
    @classmethod
    def validate_zip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", cleaned):
            raise ValueError("ZIP code must be a valid 5-digit or 9-digit US ZIP code.")
        return cleaned

    @field_validator("household_size")
    @classmethod
    def validate_household_size(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Household size must be at least 1.")
        return value

    @field_validator("num_children")
    @classmethod
    def validate_num_children(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Number of children cannot be negative.")
        return value

    @model_validator(mode="after")
    def validate_household_consistency(self) -> "EligibilityRequest":
        if self.num_children >= self.household_size:
            raise ValueError("Number of children cannot be equal to or greater than the total household size.")
        return self


class BenefitProgram(str, Enum):
    SNAP = "snap"
    MEDICAID_CHIP = "medicaid_chip"
    EITC = "eitc"
    LIHEAP = "liheap"
    WIC = "wic"

class LikelyEligible(str, Enum):
    LIKELY = "likely"
    POSSIBLY = "possibly"
    UNLIKELY = "unlikely"
    NOT_AVAILABLE_FOR_STATUS = "not_available_for_status"

class ProgramResult(BaseModel):
    program: BenefitProgram = Field(description="The benefit program evaluated")
    likely_eligible: LikelyEligible = Field(description="Likelihood of eligibility")
    reason: str = Field(description="Neutral, plain-language reason for estimation")
    source_cited: str = Field(description="Authoritative source URL or organization cited")
    apply_link: str = Field(description="Official portal link to apply in the user's state")
    as_of_date: date = Field(description="The date the grounded threshold was current")
    grounded: bool = Field(description="True if threshold came from live fetch, False if fallback")
    disclaimer: str = Field(
        default="This is an estimate, not a determination. Rules change. Only the official agency can decide.",
        description="Mandatory disclaimer statement"
    )

class SessionRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Unique session ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Session creation timestamp")
    request: EligibilityRequest = Field(description="The input eligibility request")
    results: list[ProgramResult] = Field(description="Evaluated benefit results")
