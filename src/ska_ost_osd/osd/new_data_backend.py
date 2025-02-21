"""This module concerns itself with adding new data to a current repository."""

import abc
import hashlib
import logging
import os
import shutil
import sys
import uuid
from pathlib import Path

from git import Repo
from overrides import override

from ska_telmodel.data import TMData
from ska_telmodel.data.cache import cache_path
from ska_telmodel.schema import validate

logger = logging.getLogger(__name__)


def _create_uuid_from_string(val: str):
    hex_string = hashlib.md5(val.encode("UTF-8")).hexdigest()
    return str(uuid.UUID(hex=hex_string))


class NewDataBackend:
    """Base class for the data uploading backends.

    This class is meant just as a guide to how to use the backends."""

    def __init__(self):
        pass

    @abc.abstractmethod
    def local_location(self) -> Path:
        """The location of this backend on disk."""

    @abc.abstractmethod
    def start_transaction(self, name_of_update: str) -> None:
        """Start a new session.

        :param name_of_update: A short description of the update.
        """

    @abc.abstractmethod
    def commit_transaction(self) -> None:
        """Save the current transaction and mark it as completed."""

    @abc.abstractmethod
    def add_data(self, path: Path, key: str = None) -> None:
        """Add a new data file or directory to the transaction.

        :param path: This can be either a directory of files, or a single file.
        :param key: If ``path`` is a directory, then key is used as the prefix,
            if ``path`` is a file then this is used as the key.
        """

    @abc.abstractmethod
    def status(self) -> dict[str, list[str]]:
        """Get the state of the current session"""

    @abc.abstractmethod
    def validate(self, file: Path) -> bool:
        """Validate the given file."""


class GitBackend(NewDataBackend):
    """This backend uses git as it's data source, it assumes that the
    authentication is handled on the host side.

    The `repo` should be one of (in order of preference):

        * ``ska-telescope/ska-telmodel`` (from the ssh path, this is from the
          colon to the .git)
        * ssh://git@gitlab.com:path/to/repo.git
        * https://gitlab.com/path/to/repo.git

    If ``checkout_location`` is provided that will be used instead of a temp
    directory. By default we use ``~/.ska-telmodel`` and place each checkout in
    there.
    """

    def __init__(
        self,
        repo: str = "ska-telescope/ska-telmodel-data",
        git_host: str = "gitlab.com",
    ):
        super().__init__()

        self._check_out_main_run = False

        if repo.startswith("ssh://"):
            self._uri = repo[6:]
        elif repo.startswith("https://"):
            self._uri = repo
        else:
            self._uri = f"git@{git_host}:{repo}.git"

        name = _create_uuid_from_string(self._uri)
        self._checkout_location = cache_path("git_repos", env=None) / name

        if self._checkout_location.exists():
            self._repo = Repo(self._checkout_location)
        else:
            self._repo = None
        self._checkout(switch_to_main=True)

    @override
    def local_location(self) -> Path:
        """The location of this backend on disk."""
        return self._checkout_location

    @override
    def start_transaction(
        self, name_of_update: str, create_new_branch: bool = True
    ) -> None:
        """Create a new clone (if needed), pull the main branch, and
        create a new branch.

        :param name_of_update: This will become the branch name.
        """
        self._checkout_main()
        cleaned_name = name_of_update.replace(" ", "_").lower()
        if create_new_branch:
            try:
                self._branch(cleaned_name)
            except OSError as err:
                if "does already exist" in str(err):
                    raise ValueError("Branch Already Exists")
                else:
                    raise  # pragma: no cover
        else:
            self.checkout_branch(cleaned_name)

    @override
    def commit_transaction(self) -> None:
        """Push changes to branch, if there are no local uncommitted
        changes."""

        if self.status()["is_dirty"]:
            logger.error("Files are not committed:")
            for file in self._repo.untracked_files:
                logger.error(file)
            raise ValueError(
                "Uncommitted files: " + (", ".join(self._repo.untracked_files))
            )

        self._push()

    @override
    def add_data(self, path: Path, key: str = None) -> None:
        """Copy new file into repo, and run validate on each file.

        If ``path`` is a directory, the directory structure will also be taken
        into account when creating the key.

        :param path: This can be either a directory of files, or a single file.
        :param key: If ``path`` is a directory, then key is used as the prefix,
            if ``path`` is a file then this is used as the key.
        """

        if not path.exists():
            raise ValueError("Path doesn't exist")

        if path.is_dir():
            # use the key as the starting path

            logger.info("Uploading all files in %s", str(path))
            # recursively walk and run self.add_data for each file
            base_path = path
            paths = self._walk(path)
            logger.debug("Got %d paths", len(paths))
            for current in paths:
                logger.info(
                    "Adding file %s using key=%s",
                    str(current),
                    str(current.relative_to(base_path)),
                )
                current_key = str(current.relative_to(base_path))
                if key is not None:
                    current_key = f"{key}/{current_key}"
                self.add_data(current, current_key)
            return

        if key is None:
            raise ValueError("`key` must be specified with a file")

        if Path(path).suffix != ".link" and not self.validate(path):
            raise ValueError("Validation Error")
        
        new_path = self._checkout_location / "tmdata" / key
        os.makedirs(new_path.parent, exist_ok=True)
        try:
            shutil.copy(path, new_path)
            logger.info("File copied successfully.")
        # If source and destination are same
        except shutil.SameFileError:
            logger.info("Source and destination represents the same file.")
        # If there is any permission issue
        except PermissionError:
            logger.info("Permission denied.")
        # For other errors
        except:
            logger.info("Error occurred while copying file.")	
        logger.info("path-------->> %s", path)
        logger.info("new path-------->> %s", new_path)
        logger.info("changed path-------->> %s", new_path.relative_to(self._checkout_location))
        with open(new_path) as f:
            logger.info("file content in _add method %s", f.read())
        logger.info("CALLING ADD METHID")
        self._add(new_path.relative_to(self._checkout_location))

    def commit(self, message) -> None:
        self._commit(message)

    @override
    def status(self) -> dict[str, list[str]]:
        """Get current status of all new files.

        :returns: the names of the files in different states."""

        state = {
            "is_dirty": self._repo.is_dirty(),
            "uncommitted": [item.a_path for item in self._repo.index.diff()],
            "staged": [item.a_path for item in self._repo.index.diff("HEAD")],
            "untracked": self._repo.untracked_files,
        }
        if (
            len(state["uncommitted"])
            + len(state["staged"])
            + len(state["untracked"])
            > 0
        ):
            state["is_dirty"] = True
        logger.info("log in status %s", state)  
        return state

    @override
    def validate(self, file: Path) -> bool:
        """Validates the given file. The file can be anywhere.

        :param file: The path to the file.

        :returns: Whether the file is validated or not."""

        # This might become an internal function to validate a new file
        data_library = TMData([f"file://{file.parent}"])
        # read file
        # convert to dictionary
        try:
            data = data_library[file.name].get_dict()
        except ValueError:  # pragma: no cover
            return True

        if "interface" not in data:
            logger.warning("No schema to use for validation!")
            return True

        try:
            validate(data["interface"], data, 2)
            return True
        except ValueError as e:
            logger.error(f"{e}")
            return False

    def checkout_branch(self, name):
        """Checkout named branch."""
        for head in self._repo.heads:
            if str(head) == name:
                head.checkout()
                break
        else:
            raise ValueError("No branch to checkout to could be found")

        # We should be able to do this in GitPython:
        self._repo.git.push("--set-upstream", "origin", name)
        self._pull()

    def _walk(self, path: Path) -> list[Path]:  # pragma: no cover
        """Walk through a directory, ignoring cover because of python version
        mismatches"""
        output = []
        py_version = sys.version_info
        if py_version.major >= 3 and py_version.minor >= 12:
            logger.debug("Walking using pathlib")
            for root, _, files in path.walk():
                logger.debug(root)
                for file in files:
                    output.append(root / file)
        else:
            logger.debug("Walking using os.walk")
            for dir_name, _, files in os.walk(path):
                for file in files:
                    output.append(Path(dir_name) / file)
        return output

    def _checkout(self, switch_to_main=False):
        """Make sure the repo exists, and possibly switch to the main
        branch."""
        if self._repo is None:
            logger.info("Local checkout doesn't exist, checking out...")
            self._repo = Repo.clone_from(self._uri, self._checkout_location)

        if switch_to_main:
            self._checkout_main()

    def _checkout_main(self, force: bool = False):
        if self._check_out_main_run or force:
            return
        self._check_out_main_run = True
        self._repo.remotes.origin.fetch()
        for head in self._repo.heads:
            if str(head) == "main":
                head.checkout()
                break
            elif str(head) == "master":
                head.checkout()
                break
        self._pull()

    def _pull(self):
        """Pull all latest changes from origin."""
        self._repo.remotes.origin.pull()

    def _push(self):
        """Push local changes to origin."""
        self._repo.remotes.origin.push()

    def _add(self, path):
        """Add provided path to the next commit.

        :param path: A relative path to the new file.
        """
        logger.info("added log in _add method %s", path)
        logger.info("added log in _add method %s", self.status())

        with open(path, encoding="utf-8") as f:
            logger.info("file content in _add method %s", f.read())

        self._repo.index.add([path])

    def _commit(self, message: str):
        """Commit any new changes using the given message."""
        self._repo.index.commit(message)

    def _branch(self, name):
        """Create a new branch from the main branch."""
        self._checkout_main(force=True)
        self._repo.create_head(name)
        self.checkout_branch(name)
