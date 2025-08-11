"""GitLab helper functions for OSD."""

import logging
import os
import subprocess
from pathlib import Path
from typing import List, Tuple

from ska_telmodel.data.new_data_backend import GitBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory.

    :return: Path, the absolute path to the project root directory.
    """
    current_dir = Path(__file__).resolve().parent.parent
    return current_dir.parent.parent.parent


def check_file_modified(file_path: Path) -> bool:
    """Check if a file has been modified by comparing its size with the
    original.

    :param file_path: Path, the path to the file to check.
    :return: bool, True if the file was modified, False otherwise.
    """
    if not file_path.exists():
        return False

    # Get file stats
    stats = os.stat(file_path)

    # TODO: Implement a more robust way to check modifications
    # For now, we'll assume any file with content is modified
    return stats.st_size > 0


def setup_gitlab_access():
    """Set up GitLab SSH access with proper host key verification.

    This function configures the local SSH environment so that the system can
    securely connect to GitLab via SSH. It ensures that the `.ssh` directory
    exists with the correct permissions, adds GitLab's host key to the
    `known_hosts` file for host verification, and writes a private SSH key
    (retrieved from the `ID_RSA` environment variable) to the `id_rsa` file.

    :return: None
    """
    ssh_dir = Path.home() / ".ssh"
    known_hosts_file = ssh_dir / "known_hosts"

    try:
        # Create .ssh directory with correct permissions
        if ssh_dir.exists():
            ssh_dir.mkdir(mode=0o700, exist_ok=True)

        # Add GitLab's host key using ssh-keyscan
        subprocess.run(
            ["ssh-keyscan", "gitlab.com"],
            stdout=known_hosts_file.open("a"),
            stderr=subprocess.PIPE,
            check=True,
        )
        known_hosts_file.chmod(0o600)

        # If using SSH key from vault or environment
        ssh_key = os.getenv("ID_RSA")
        if ssh_key is None:
            raise ValueError("ID_RSA environment variable not set")
        key_file = ssh_dir / "id_rsa"
        key_file.write_text(ssh_key)
        key_file.chmod(0o600)
    except Exception as e:
        logger.error("Failed to setup GitLab SSH access: %s", str(e))
        raise


def push_to_gitlab(
    files_to_add: List[Tuple[Path, str]], commit_msg: str, branch_name: str = None
) -> None:
    """Push modified files to a GitLab repository.

    This function automates the process of pushing files to a GitLab
    repository. It sets up SSH access to GitLab, optionally creates or
    switches to a branch, filters the given file list to include only
    modified files, stages them in the repository, commits with the
    given message, and pushes to GitLab.

    If a branch name is provided and does not exist, a new branch will
    be created. If it already exists, the function will log an error and
    check out the same branch.

    :param files_to_add: List[Tuple[Path, str]], a list of tuples where
        each tuple contains (source_path, target_path) for files to be
        committed.
    :param commit_msg: str, the commit message to use.
    :param branch_name: str, optional branch name to create or switch to
        before committing.
    :return: None
    :raises GitLabError: If there are any issues with GitLab operations.
    :raises ValueError: If the branch already exists or if other
        validation errors occur.
    """
    repo = "ska-telescope/ost/ska-ost-osd"
    id_rsa_path = Path.home() / ".ssh/id_rsa"

    try:
        setup_gitlab_access()
        git_repo = GitBackend(repo=repo)

        # # Filter and add only modified files
        if branch_name:
            try:
                git_repo.start_transaction(branch_name, create_new_branch=True)
            except ValueError as err:
                if str(err) == "Branch Already Exists":
                    logger.error("Branch already exists, try a different branch name")
                    git_repo.checkout_branch(branch_name)
                    logger.error("Checking out same branch")

        modified_files = []
        for src_path, target_path in files_to_add:
            if check_file_modified(src_path):
                modified_files.append((src_path, target_path))
            else:
                logger.info("Skipping unmodified file: %s", src_path)

        if not modified_files:
            logger.info("No modified files to push")
            return

        try:
            # Add files
            for src_path, target_path in modified_files:
                current_dir = Path(__file__).resolve().parent
                project_root = current_dir.parent.parent.parent
                src_path = project_root / src_path
                if src_path.name == "mid_capabilities.json":
                    src_path = Path("tmdata/ska1_mid/mid_capabilities.json")
                git_repo.add_data(src_path, target_path)

            # Commit and push
            git_repo.commit(commit_msg)
            git_repo.commit_transaction()
        except Exception as e:
            logger.error("GitLab operation failed: %s", str(e))
            raise

    except Exception as e:
        logger.error("Failed to push to GitLab: %s", str(e))
        raise
    finally:
        if id_rsa_path.exists():
            try:
                id_rsa_path.unlink()
                logger.info("Successfully removed id_rsa file")
            except (OSError, IOError) as e:
                logger.error("Failed to remove id_rsa file: %s", str(e))
