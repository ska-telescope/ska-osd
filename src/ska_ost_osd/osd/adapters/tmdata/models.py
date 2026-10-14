"""The storage models: each tmdata file as it is stored, validated as a
whole. ``storage`` reads the files into these, and ``TMDataRepository`` maps
them to the reader models."""

import re
from typing import Any, Literal, Self

from pydantic import AliasChoices, Field, model_validator

from ska_ost_osd.osd.common.constant import ARRAY_ASSEMBLY_PATTERN
from ska_ost_osd.osd.models.capabilities import (
    LowBasicCapabilities,
    LowCapabilitySet,
    MidBasicCapabilities,
    MidCapabilitySet,
)
from ska_ost_osd.osd.models.cycles import (
    CycleID,
    CycleInformation,
    CyclePolicies,
    TelescopeCapabilities,
)
from ska_ost_osd.osd.models.defaults import (
    LowQualityAttributeMetrics,
    OSDBaseModel,
    SPFRxParameters,
)
from ska_ost_osd.osd.models.subarray_templates import SubarrayTemplate


class ElevationConstraints(OSDBaseModel):
    min_elevation_deg: float = Field(ge=0, le=90, examples=[45.0])
    max_elevation_deg: float = Field(ge=0, le=90, examples=[90.0])

    @model_validator(mode="after")
    def check_elevation_range(self) -> Self:
        if self.min_elevation_deg > self.max_elevation_deg:
            raise ValueError("min_elevation_deg must not exceed max_elevation_deg")
        return self


class TelescopeCapabilitiesFileBase(OSDBaseModel):
    """Base for the Mid and Low capabilities file models."""

    constraints: ElevationConstraints

    @model_validator(mode="before")
    @classmethod
    def collect_subarrays(cls, data: Any) -> Any:
        """
        In the tmdata file each array assembly is a top-level key;
        gather the keys matching ``ARRAY_ASSEMBLY_PATTERN`` into
        ``subarrays``, using the key as the subarray name.

        The pattern separates the array assemblies from the file's other
        top-level keys.
        """
        if not isinstance(data, dict) or "subarrays" in data:
            return data
        data = data.copy()
        data["subarrays"] = [
            {"name": key, **data.pop(key)}
            for key in list(data)
            if re.match(ARRAY_ASSEMBLY_PATTERN, key)
        ]
        return data


class MidCapabilitiesFile(TelescopeCapabilitiesFileBase):
    """Top-level model for mid_capabilities.json."""

    telescope: Literal["Mid"] = "Mid"
    basic_capabilities: MidBasicCapabilities
    subarrays: list[MidCapabilitySet]

    @model_validator(mode="after")
    def check_available_receivers(self) -> Self:
        rx_ids = {band.rx_id for band in self.basic_capabilities.frequency_bands}
        for subarray in self.subarrays:
            unknown = set(subarray.available_receivers) - rx_ids
            if unknown:
                raise ValueError(
                    f"{subarray.name}: available_receivers {sorted(unknown)} "
                    "not found in frequency_bands"
                )
        return self


class LowCapabilitiesFile(TelescopeCapabilitiesFileBase):
    """Top-level model for low_capabilities.json."""

    telescope: Literal["Low"] = "Low"
    basic_capabilities: LowBasicCapabilities
    subarrays: list[LowCapabilitySet]


class AvoidanceConstraints(OSDBaseModel):
    """
    Sun, moon and Jupiter avoidance angles.
    """

    sun_avoidance_angle_deg: float = Field(examples=[30.0])
    moon_avoidance_angle_deg: float = Field(examples=[10.0])
    jupiter_avoidance_angle_deg: float = Field(examples=[10.0])


class TelescopeDefaultsFileBase(OSDBaseModel):
    """Base for the Mid and Low defaults file models."""

    constraints: AvoidanceConstraints


class MidDefaultsFile(TelescopeDefaultsFileBase):
    """Top-level model for mid_defaults.json."""

    telescope: Literal["Mid"] = "Mid"
    spfrx_defaults: SPFRxParameters = Field(
        validation_alias=AliasChoices("spfrx_defaults", "defaults")
    )


class LowDefaultsFile(TelescopeDefaultsFileBase):
    """Top-level model for low_defaults.json."""

    telescope: Literal["Low"] = "Low"
    quality_attribute_metrics: LowQualityAttributeMetrics


class CycleFile(OSDBaseModel):
    """Top-level model for cycles/cycle_<N>.json, and for the legacy
    observatory_policies.json."""

    cycle_number: CycleID
    cycle_id: str | None = None
    type: str | None = Field(default=None, examples=["Science Verification"])
    cycle_description: str
    cycle_information: CycleInformation
    cycle_policies: CyclePolicies
    telescope_capabilities: TelescopeCapabilities


class SubarrayTemplateLibraryFile(OSDBaseModel):
    """Top-level model for subarray_template_library.json."""

    templates: list[SubarrayTemplate]

    @model_validator(mode="before")
    @classmethod
    def collect_templates(cls, data: Any) -> Any:
        """In tmdata each template is a top-level key; gather them into
        ``templates``, using the key as the template name."""
        if not isinstance(data, dict) or "templates" in data:
            return data
        return {
            "templates": [{"name": name, **template} for name, template in data.items()]
        }
