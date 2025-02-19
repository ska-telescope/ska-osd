"""GitLab helper functions for OSD."""
import logging
import os
import sys
import subprocess

from pathlib import Path
from typing import List, Tuple

from ska_telmodel.data.new_data_backend import GitBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    current_dir = Path(__file__).resolve().parent
    return current_dir.parent.parent.parent


def check_file_modified(file_path: Path) -> bool:
    """Check if a file has been modified by comparing its size with the original.

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if file was modified, False otherwise
    """
    if not file_path.exists():
        return False

    # Get file stats
    stats = os.stat(file_path)

    # TODO: Implement a more robust way to check modifications
    # For now, we'll assume any file with content is modified
    return stats.st_size > 0


def setup_gitlab_access():
    """
    Set up GitLab SSH access with proper host key verification
    """
    ssh_dir = Path('/home/tango/.ssh')
    known_hosts_file = ssh_dir / 'known_hosts'

    try:
        # Create .ssh directory with correct permissions
        ssh_dir.mkdir(mode=0o700, exist_ok=True)

        # Add GitLab's host key using ssh-keyscan
        subprocess.run(
            ['ssh-keyscan', 'gitlab.com'],
            stdout=known_hosts_file.open('a'),
            stderr=subprocess.PIPE,
            check=True
        )
        known_hosts_file.chmod(0o600)

        # If using SSH key from vault or environment
        ssh_key = os.getenv('ID_RSA')
        key_file = ssh_dir / 'id_rsa'
        key_file.write_text(ssh_key)
        key_file.chmod(0o600)
    except Exception as e:
        logger.error(f"Failed to setup GitLab SSH access: {str(e)}")
        raise

def push_to_gitlab(
    files_to_add: List[Tuple[Path, str]], commit_msg: str, branch_name: str = None
) -> None:
    """Push files to GitLab repository.

    Args:
        files_to_add: List of tuples containing (source_path, target_path)
        commit_msg: Commit message
        branch: Branch name
    """
    repo = "ska-telescope/ost/ska-ost-osd"
    setup_gitlab_access()
    git_repo = GitBackend(repo=repo)

    # Filter and add only modified files
    if branch_name:
        try:
            git_repo.start_transaction(branch_name, create_new_branch=True)
        except ValueError as err:
            if str(err) == "Branch Already Exists":
                print("Branch already exists, try a different branch name")
                sys.exit(1)
            else:
                raise
    modified_files = []

    for src_path, target_path in files_to_add:
        if check_file_modified(src_path):
            modified_files.append((src_path, target_path))
        else:
            logger.info("Skipping unmodified file: %s", src_path)

    if not modified_files:
        logger.info("No modified files to push")
        return

    # Add files
    for src_path, target_path in modified_files:
        git_repo.add_data(src_path, target_path)

    # Commit and push
    git_repo.commit(commit_msg)
    git_repo.commit_transaction()
