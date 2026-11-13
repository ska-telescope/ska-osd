from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from ska_ost_osd.osd.common.constant import Telescope
from ska_ost_osd.osd.models.defaults import OSDBaseModel


class PolicyType(StrEnum):
    SCIENCE_VERIFICATION = "science_verification"
    SHARED_RISK = "shared_risk"
    STANDARD_OPERATIONS = "standard_operations"


class ProposalWindow(OSDBaseModel):
    opens: AwareDatetime = Field(examples=["2026-03-27T12:00:00.000Z"])
    closes: AwareDatetime = Field(examples=["2027-04-01T15:00:00.000Z"])

    @model_validator(mode="after")
    def check_opens_before_closes(self) -> Self:
        if self.opens >= self.closes:
            raise ValueError("the proposal window must open before it closes")
        return self


class ProposalPolicy(OSDBaseModel):
    """What one proposal in the cycle may ask for."""

    max_observing_hours: float = Field(ge=0, examples=[100.0])
    max_targets: int | None = Field(default=None, ge=0)
    max_observation_setups: int | None = Field(default=None, ge=0)
    max_data_products: int | None = Field(default=None, ge=0)


class TelescopeCapabilities(OSDBaseModel):
    """What a cycle offers on one telescope: its array assembly, and the
    policy offered for each type, by policy ID."""

    array_assembly: str = Field(examples=["AA2"])
    policies: dict[PolicyType, str] = Field(
        min_length=1, examples=[{"science_verification": "AA2_SV"}]
    )


class Cycle(OSDBaseModel):
    """One cycle: its metadata, proposal window and policy, and what it offers
    on each telescope."""

    cycle_id: str
    name: str
    description: str
    cycle_number: int | None = Field(default=None, ge=0, examples=[1])
    proposal_window: ProposalWindow
    proposal_policy: ProposalPolicy
    capabilities: dict[Telescope, TelescopeCapabilities] = Field(min_length=1)
