import json
import os

import pytest
from ska_telmodel_client import TMData

from ska_ost_osd.osd.adapters.tmdata import TMDataRepository


@pytest.fixture(scope="session")
def tests_tmdata_source():
    """TMData source URL fixture."""
    return f"file://{os.path.join(os.path.dirname(__file__), 'tmdata')}"


@pytest.fixture(scope="session")
def tests_tmdata(tests_tmdata_source):
    return TMData(source_uris=[tests_tmdata_source])


@pytest.fixture(scope="session")
def empty_tmdata(tmp_path_factory):
    """Fixture for an empty TMData instance."""
    empty_dir = tmp_path_factory.mktemp("empty_tmdata")
    return TMData([f"file://{empty_dir}"])


@pytest.fixture(scope="session")
def test_tmdata_repository(tests_tmdata):
    """The OSD repository over the test copy of the tmdata."""
    return TMDataRepository(tests_tmdata)


@pytest.fixture(scope="session")
def empty_tmdata_repository(empty_tmdata):
    """The OSD repository over TMData with no files."""
    return TMDataRepository(empty_tmdata)


@pytest.fixture
def tmdata_repository_with(tests_tmdata_source, tmp_path):
    """Build an OSD repository over the test copy of the tmdata, with some
    files replaced: pass a dict of each file's tmdata path to its contents.
    The replacements are written to a temporary source listed after the
    test tmdata, so they take precedence."""

    def _tmdata_repository_with(files: dict[str, dict]) -> TMDataRepository:
        for path, content in files.items():
            (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / path).write_text(json.dumps(content))
        return TMDataRepository(TMData([tests_tmdata_source, f"file://{tmp_path}"]))

    return _tmdata_repository_with
