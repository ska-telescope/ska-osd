from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from ska_ost_osd.osd.models.defaults import OSDBaseModel


class CycleInformation(OSDBaseModel):
    cycle_id: str = Field(examples=["SKAO_2027_1"])
    proposal_open: AwareDatetime = Field(examples=["2026-03-27T12:00:00.000Z"])
    proposal_close: AwareDatetime = Field(examples=["2027-04-01T15:00:00.000Z"])

    @model_validator(mode="after")
    def check_proposal_window(self) -> Self:
        if self.proposal_open >= self.proposal_close:
            raise ValueError("proposal_open must be before proposal_close")
        return self


class CyclePolicies(OSDBaseModel):
    normal_max_hours: float = Field(ge=0, examples=[100.0])
    max_targets: int | None = Field(default=None, ge=0)
    max_observation_setups: int | None = Field(default=None, ge=0)
    max_data_products: int | None = Field(default=None, ge=0)


class TelescopeCapabilities(OSDBaseModel):
    """The array assembly each telescope offers in the cycle, or ``None``."""

    ska_mid: str | None = Field(default=None, alias="Mid", examples=["AA2"])
    ska_low: str | None = Field(default=None, alias="Low", examples=["AA2_SV"])


class ObservatoryPolicy(OSDBaseModel):
    """Top-level model for observatory_policies.json."""

    cycle_number: int = Field(ge=1, examples=[1])
    cycle_id: str | None = None
    type: str | None = Field(default=None, examples=["Science Verification"])
    cycle_description: str
    cycle_information: CycleInformation
    cycle_policies: CyclePolicies
    telescope_capabilities: TelescopeCapabilities
