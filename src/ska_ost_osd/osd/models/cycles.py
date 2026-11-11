from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from ska_ost_osd.osd.models.defaults import OSDBaseModel


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
    """The array assembly each telescope offers in the cycle, or ``None``."""

    ska_mid: str | None = Field(default=None, examples=["AA2"])
    ska_low: str | None = Field(default=None, examples=["AA2"])


class Cycle(OSDBaseModel):
    """One cycle: its metadata, proposal dates, policies and the capability
    set each telescope offers."""

    id: str
    name: str
    description: str
    number: int = Field(ge=0, examples=[1])
    type: str | None = Field(default=None, examples=["Science Verification"])
    proposal_window: ProposalWindow
    proposal_policy: ProposalPolicy
    telescope_capabilities: TelescopeCapabilities
