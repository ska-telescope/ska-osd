import logging
import posixpath
from functools import cached_property
from typing import Any, Dict, Optional

from ska_telmodel_client import TMData

from ska_ost_osd.osd.common.osd_validation_messages import (
    ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE,
    ARRAY_ASSEMBLY_DOESNOT_MATCH_CYCLE_CAPABILITY_ERROR_MESSAGE,
    ARRAY_ASSEMBLY_REQUIRES_CAPABILITY_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_BELONG_TO_CYCLE_ERROR_MESSAGE,
    CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE,
    CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE,
    CYCLE_ID_ERROR_MESSAGE,
)

from .adapters.tmdata.storage import get_cycle_paths, get_policy_paths
from .common.constant import (
    RELEASE_FILE_PATH_LATEST,
    Telescope,
    osd_file_mapping,
)
from .models.capabilities import merge_capabilities
from .models.cycles import PolicyType

LOGGER = logging.getLogger(__name__)

# The telescope names the capability documents and responses use
_LEGACY_TELESCOPE_NAMES = {
    Telescope.SKA_MID: "mid",
    Telescope.SKA_LOW: "low",
}

# The legacy names of the cycle file fields, in the order the legacy response
# serves them. A field not listed, such as name, is not served.
_LEGACY_CYCLE_FIELD_NAMES = {
    "number": "cycle_number",
    "id": "cycle_id",
    "type": "type",
    "description": "cycle_description",
    "proposal_window": "cycle_information",
    "proposal_policy": "cycle_policies",
    "capabilities": "telescope_capabilities",
}

# A frozen copy of the PHT view's type names, which will change when the PHT
# reads the policy types
_LEGACY_TYPE_NAMES = {
    PolicyType.SCIENCE_VERIFICATION: "Science Verification",
    PolicyType.SHARED_RISK: "Shared Risk",
    PolicyType.STANDARD_OPERATIONS: "Proposal",
}


class OSD:
    """Build OSD responses from telescope capability documents and cycle definitions."""

    def __init__(
        self,
        telescope: Telescope | None,
        array_assembly: str,
        tmdata: TMData,
        cycle_id: int,
        process_templates: bool = False,
    ) -> None:
        """Initialize the OSD class.

        :param telescope: requested telescope, ``Telescope.SKA_MID`` or
            ``Telescope.SKA_LOW``. The legacy names ``"mid"`` and ``"low"``
            are still accepted.
        :param array_assembly: requested array assembly name, such as ``"AA2"``.
        :param tmdata: TMData, TMData class object.
        :param cycle_id: int, cycle identifier.
        :param process_templates: bool, whether to process template mappings.
        :return: None
        """
        self.cycle_id = cycle_id
        self.requested_telescope = _LEGACY_TELESCOPE_NAMES.get(telescope, telescope)
        self.requested_array_assembly = array_assembly
        self.tmdata = tmdata
        self.process_templates = process_templates

    @cached_property
    def capability_filepaths(self) -> dict[str, str]:
        """Return telescope-keyed TMData basic capabilities paths, e.g.
        ``{"mid": "telescopes/ska_mid/basic_capabilities.json"}``."""
        return {
            posixpath.basename(posixpath.dirname(entry)).removeprefix("ska_"): entry
            for entry in self.tmdata
            if entry.endswith("/basic_capabilities.json")
        }

    def cycle_filepaths(self) -> dict[int, str]:
        """Return the TMData cycle file paths keyed by the ``number`` in each
        file, which the legacy OSD API looks cycles up by. A cycle without a
        number can't be selected."""
        numbers = (
            (self.tmdata[path].get_dict().get("number"), path)
            for path in get_cycle_paths(self.tmdata).values()
        )
        return dict(sorted((n, path) for n, path in numbers if n is not None))

    def get_available_cycles(self) -> list[int]:
        """List available cycle IDs from the observing-cycle files."""
        return list(self.cycle_filepaths())

    def check_cycle_id(self) -> str | None:
        """Return an error message when the selected cycle file is absent."""
        if self.cycle_id is None:
            return None

        if self.cycle_id not in self.cycle_filepaths():
            cycle_numbers = ",".join(
                str(cycle) for cycle in self.get_available_cycles()
            )
            return CYCLE_ID_ERROR_MESSAGE.format(self.cycle_id, cycle_numbers)
        return None

    def validate_query(self) -> str | None:
        """Validate the query before reading TMData files."""
        capability_filepaths = self.capability_filepaths
        if self.requested_telescope:
            # A queried telescope must have a corresponding capability document.
            if self.requested_telescope.lower() not in capability_filepaths:
                available = ", ".join(list(osd_file_mapping.keys())[:3])
                return CAPABILITY_DOESNOT_EXIST_ERROR_MESSAGE.format(
                    self.requested_telescope, available
                )

        # Named capabilities can only be queried with a telescope.
        if self.requested_array_assembly and not self.requested_telescope:
            if self.cycle_id is not None:
                return CYCLE_ID_ARRAY_ASSEMBLY_ERROR_MESSAGE
            return ARRAY_ASSEMBLY_REQUIRES_CAPABILITY_ERROR_MESSAGE
        return None

    def get_cycle_definition(self) -> tuple[dict[str, Any] | None, str | None]:
        """Load the selected cycle definition after checking it exists."""
        cycle_error = self.check_cycle_id()
        if cycle_error:
            return None, cycle_error
        if self.cycle_id is None:
            return None, None
        cycle = self.tmdata[self.cycle_filepaths()[self.cycle_id]].get_dict()
        # The legacy response has one type for the whole cycle
        types = {
            policy_type
            for offered in cycle["capabilities"].values()
            for policy_type in offered["policies"]
        }
        if len(types) != 1:
            return None, (
                f"Cycle {self.cycle_id} offers more than one policy type, which "
                "the legacy OSD API can't serve"
            )
        (cycle["type"],) = types
        cycle_definition = {
            legacy_name: cycle[name]
            for name, legacy_name in _LEGACY_CYCLE_FIELD_NAMES.items()
            if name in cycle
        }
        cycle_definition["type"] = _LEGACY_TYPE_NAMES[cycle["type"]]
        cycle_definition["cycle_information"] = {
            "cycle_id": cycle["id"],
            "proposal_open": cycle["proposal_window"]["opens"],
            "proposal_close": cycle["proposal_window"]["closes"],
        }
        cycle_definition["cycle_policies"] = {
            ("normal_max_hours" if name == "max_observing_hours" else name): value
            for name, value in cycle["proposal_policy"].items()
        }
        # The cycle files name the telescopes by Telescope value; the legacy
        # response names them Mid and Low
        cycle_definition["telescope_capabilities"] = {
            _LEGACY_TELESCOPE_NAMES[Telescope(telescope)].capitalize(): offered[
                "policies"
            ][cycle["type"]]
            for telescope, offered in cycle_definition["telescope_capabilities"].items()
        }
        return cycle_definition, None

    def select_telescope_capabilities(
        self, cycle_definition: dict[str, Any] | None
    ) -> tuple[dict[str, str | None] | None, str | None]:
        """Select the named capabilities for each included telescope."""
        if cycle_definition is None:
            # Catalogue mode: select each requested telescope and optionally one
            # array assembly. No array assembly filter is expanded to all
            # named capabilities later in build_osd_data().
            if self.requested_telescope:
                return {
                    self.requested_telescope.lower(): self.requested_array_assembly
                }, None
            return {
                telescope.lower(): self.requested_array_assembly
                for telescope in self.capability_filepaths
            }, None

        # Cycle mode: each telescope maps to the capabilities the cycle prescribes.
        cycle_telescope_capabilities = cycle_definition["telescope_capabilities"]
        if self.requested_telescope is None:
            return {
                telescope.lower(): name
                for telescope, name in cycle_telescope_capabilities.items()
            }, None

        telescope_key = self.requested_telescope.capitalize()
        # A requested telescope must be specified in the requested cycle.
        if telescope_key not in cycle_telescope_capabilities:
            available = ", ".join(
                available_telescope.lower()
                for available_telescope in cycle_telescope_capabilities
            )
            return None, CAPABILITY_DOESNOT_BELONG_TO_CYCLE_ERROR_MESSAGE.format(
                self.requested_telescope, self.cycle_id, available
            )

        cycle_capabilities_name = cycle_telescope_capabilities[telescope_key]
        if self.requested_array_assembly:
            # A cycle already specifies the capabilities for each telescope.
            # Requesting an array assembly is valid only when it matches the cycle.
            if self.requested_array_assembly != cycle_capabilities_name:
                return (
                    None,
                    ARRAY_ASSEMBLY_DOESNOT_MATCH_CYCLE_CAPABILITY_ERROR_MESSAGE.format(
                        self.requested_array_assembly,
                        self.requested_telescope,
                        self.cycle_id,
                        cycle_capabilities_name,
                    ),
                )
            LOGGER.warning(
                "Ignoring redundant array assembly %s for capability %s in cycle %s",
                self.requested_array_assembly,
                self.requested_telescope,
                self.cycle_id,
            )

        # Join the telescope to the capabilities specified in the cycle.
        return {self.requested_telescope.lower(): cycle_capabilities_name}, None

    def get_telescope_capability_data(self, telescope: str) -> dict[str, Any]:
        """Load one telescope capability document and optional template mappings.

        The document is rebuilt in its legacy shape: the basic capabilities,
        without the elevation limits, as Mid's ``receiver_information`` or
        Low's one band, and the capabilities of each array assembly and policy."""
        capability_filepath = self.capability_filepaths[telescope]
        telescope_dir = posixpath.dirname(capability_filepath)
        stored = self.tmdata[capability_filepath].get_dict()
        if telescope == "mid":
            basic_capabilities = {"receiver_information": stored["frequency_bands"]}
        else:
            # Low's band is also served with its coarse channels and the
            # channels each mode divides them into
            coarse_channels, modes = stored["coarse_channels"], stored["modes"]
            basic_capabilities = stored["frequency_band"] | {
                "min_coarse_channel": coarse_channels["min"],
                "max_coarse_channel": coarse_channels["max"],
                "coarse_channel_width_hz": coarse_channels["width_hz"],
                "number_continuum_channels_per_coarse_channel": modes["continuum"][
                    "channels_per_coarse_channel"
                ],
                "number_zoom_channels_per_coarse_channel": modes["spectral"][
                    "channels_per_coarse_channel"
                ],
                "number_pst_channels_per_coarse_channel": modes["pst"][
                    "channels_per_coarse_channel"
                ],
                "number_pss_channels_per_coarse_channel": modes["pss"][
                    "channels_per_coarse_channel"
                ],
            }
        return {
            "basic_capabilities": basic_capabilities,
            **{
                name: self._legacy_capabilities(telescope_dir, capabilities)
                for name, capabilities in self._stored_capabilities(
                    telescope_dir
                ).items()
            },
        }

    def _stored_capabilities(self, telescope_dir: str) -> dict[str, dict[str, Any]]:
        """The telescope's capabilities as stored, by name: each array
        assembly, and each policy a cycle names, applied to that cycle's
        array assembly."""
        directory = f"{telescope_dir}/array_assemblies"
        array_assemblies = {
            array_assembly["array_assembly"]: array_assembly
            for array_assembly in (
                self.tmdata[f"{directory}/{name}"].get_dict()
                for name in self.tmdata[directory]
            )
        }
        telescope = Telescope(posixpath.basename(telescope_dir))
        policies = {}
        for path in get_cycle_paths(self.tmdata).values():
            offered = self.tmdata[path].get_dict()["capabilities"].get(telescope)
            if offered is None:
                continue
            for policy_id in offered["policies"].values():
                policy_path = get_policy_paths(self.tmdata, telescope)[policy_id]
                policy = self.tmdata[policy_path].get_dict()
                del policy["policy"]
                # The legacy response serves the basic capabilities apart
                policies[policy_id] = merge_capabilities(
                    {}, array_assemblies[offered["array_assembly"]], policy
                )
        return dict(sorted((array_assemblies | policies).items()))

    def _legacy_capabilities(
        self, telescope_dir: str, capabilities: dict[str, Any]
    ) -> dict[str, Any]:
        """Capabilities in their legacy shape: the array assembly as a template
        pattern, or as that array assembly's templates when they are processed."""
        capabilities = dict(capabilities)
        # The legacy response serves the stations or dishes flat, with their
        # IDs as number_station_ids or number_dish_ids
        if "stations" in capabilities:
            stations = capabilities.pop("stations")
            capabilities["number_stations"] = stations["number_stations"]
            capabilities["max_baseline_km"] = stations["max_baseline_km"]
            capabilities["number_station_ids"] = stations["ids"]
        if "dishes" in capabilities:
            dishes = capabilities.pop("dishes")
            capabilities["number_ska_dishes"] = dishes["number_ska_dishes"]
            capabilities["number_meerkat_dishes"] = dishes["number_meerkat_dishes"]
            capabilities["number_meerkatplus_dishes"] = dishes[
                "number_meerkatplus_dishes"
            ]
            capabilities["max_baseline_km"] = dishes["max_baseline_km"]
            capabilities["number_dish_ids"] = dishes["ids"]
        if "receivers" in capabilities:
            capabilities["available_receivers"] = capabilities.pop("receivers")
        # Mid's channel widths are also served without the _hz suffix
        if "allowed_channel_width_values_hz" in capabilities:
            capabilities["allowed_channel_width_values"] = capabilities[
                "allowed_channel_width_values_hz"
            ]
        # The modes, and Low's subarray beams, are served flat under
        # their legacy names
        modes = capabilities.pop("modes")
        capabilities["number_zoom_windows"] = modes["spectral"]["max_zoom_windows"]
        capabilities["number_zoom_channels"] = modes["spectral"]["max_zoom_channels"]
        if "zoom_factors" in modes["spectral"]:
            capabilities["allowed_zoom_factors"] = modes["spectral"]["zoom_factors"]
        capabilities["number_pss_beams"] = modes["pss"]["max_beams"]
        capabilities["ps_beam_bandwidth_hz"] = modes["pss"]["beam_bandwidth_hz"]
        capabilities["number_pst_beams"] = modes["pst"]["max_beams"]
        if "vlbi" in modes:
            capabilities["number_vlbi_beams"] = modes["vlbi"]["max_beams"]
        if "subarray_beams" in capabilities:
            subarray_beams = capabilities.pop("subarray_beams")
            capabilities["number_substations"] = subarray_beams[
                "max_substations_per_subarray_beam"
            ]
            capabilities["number_subarray_beams"] = subarray_beams["max_subarray_beams"]
        array_assembly = capabilities.pop("array_assembly")
        if not self.process_templates:
            capabilities["subarray_templates"] = [f"*_{array_assembly}"]
            return capabilities
        templates_dir = f"{telescope_dir}/{osd_file_mapping['subarray_templates']}"
        try:
            templates = self.tmdata[f"{templates_dir}/{array_assembly}.json"].get_dict()
        except KeyError:
            return capabilities
        # Keyed by name, with the stations as one comma-separated string
        capabilities["subarray_templates"] = {
            template.pop("name"): {
                **template,
                "custom_stations": ",".join(template["custom_stations"]),
            }
            for template in templates["templates"]
        }
        return capabilities

    def check_capabilities(
        self, name: str, telescope_capability_data: dict[str, Any]
    ) -> str | None:
        """Return an error when the named capabilities are absent from a
        telescope."""
        if (
            name in ("constraints", "basic_capabilities")
            or name not in telescope_capability_data
        ):
            available = ", ".join(
                key
                for key in telescope_capability_data
                if key not in ("telescope", "basic_capabilities", "constraints")
            )
            return ARRAY_ASSEMBLY_DOESNOT_EXIST_ERROR_MESSAGE.format(name, available)
        return None

    def build_osd_data(
        self,
        selected_names: dict[str, str | None],
        cycle_definition: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """Materialize the selected telescope capabilities."""
        result_data = {"capabilities": {}}
        errors = []

        for telescope, name in selected_names.items():
            telescope_capability_data = self.get_telescope_capability_data(telescope)
            selected_data = {
                "basic_capabilities": telescope_capability_data["basic_capabilities"]
            }

            if name is None:
                # An unfiltered catalogue response contains all named capabilities.
                selected_data.update(
                    {
                        key: value
                        for key, value in telescope_capability_data.items()
                        if key not in ("telescope", "basic_capabilities", "constraints")
                    }
                )
            else:
                capabilities_error = self.check_capabilities(
                    name, telescope_capability_data
                )
                if capabilities_error:
                    errors.append(capabilities_error)
                    continue
                selected_data[name] = telescope_capability_data[name]

            result_data["capabilities"][telescope] = selected_data

        if errors:
            return None, errors
        if cycle_definition is not None:
            result_data = {"observatory_policy": cycle_definition, **result_data}
        return result_data, []

    def get_osd_data(self) -> tuple[dict[str, Any] | None, list[str]]:
        """Return OSD data selected by the query's cycle and telescope filters."""
        query_error = self.validate_query()
        if query_error:
            return None, [query_error]

        cycle_definition, cycle_error = self.get_cycle_definition()
        if cycle_error:
            return None, [cycle_error]

        selected_names, selection_error = self.select_telescope_capabilities(
            cycle_definition
        )
        if selection_error:
            return None, [selection_error]

        return self.build_osd_data(selected_names, cycle_definition)


def get_available_cycles(tmdata: TMData) -> list[int]:
    """List available cycle IDs from observing-cycle file names."""
    return OSD(
        telescope=None,
        array_assembly=None,
        tmdata=tmdata,
        cycle_id=None,
    ).get_available_cycles()


def get_osd_latest_version(tmdata_version: TMData) -> str:
    """Read the latest_release.txt file and retrieve the latest OSD version.

    :param tmdata_version: TMData, TMData object for gitlab main version files.
    :return: str, the latest OSD release version.
    """
    osd_version = (
        tmdata_version[RELEASE_FILE_PATH_LATEST].get().decode("utf-8").replace('"', "")
    )

    return osd_version


def get_osd_data(
    telescope: Telescope | None = None,
    array_assembly: str = None,
    tmdata: TMData = None,
    cycle_id: int = None,
    process_templates: bool = False,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Build OSD data for telescope and named array assembly query filters.

    :param telescope: optional telescope name.
    :param array_assembly: optional name of an array assembly.
    :param tmdata: TMData object containing the OSD documents.
    :param cycle_id: optional observing-cycle ID.
    :param process_templates: whether to process template mappings.
    :return: OSD data and any validation errors.
    """
    osd_data, data_error_msg_list = OSD(
        telescope=telescope,
        array_assembly=array_assembly,
        tmdata=tmdata,
        cycle_id=cycle_id,
        process_templates=process_templates,
    ).get_osd_data()

    return osd_data, data_error_msg_list


def get_osd_using_tmdata(
    tm_data: TMData,
    telescope: Telescope | None = None,
    array_assembly: Optional[str] = None,
    cycle_id: Optional[int] = None,
    process_templates: bool = False,
) -> Dict:
    """Retrieve OSD data using an already constructed TMData object.

    :param tm_data: TMData, pre-resolved TMData source for OSD retrieval.
    :param telescope: optional telescope name.
    :param array_assembly: optional name of an array assembly.
    :param cycle_id: int, optional cycle ID.
    :param process_templates: bool, whether to process template mappings.
    :return: Dict[Dict[str, Any]], OSD data.
    :raises ValueError: If any validation or processing errors occur.
    """
    errors = []

    osd_data, osd_errors = get_osd_data(
        telescope=telescope,
        tmdata=tm_data,
        array_assembly=array_assembly,
        cycle_id=cycle_id,
        process_templates=process_templates,
    )
    errors.extend(osd_errors)
    if errors:
        raise ValueError(errors)

    return osd_data
