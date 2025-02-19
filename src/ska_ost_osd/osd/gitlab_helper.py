"""GitLab helper functions for OSD."""
import logging
import os
from os import getenv
import sys
from pathlib import Path
from typing import List, Tuple

from ska_telmodel.data.new_data_backend import GitBackend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import subprocess
import logging

logger = logging.getLogger(__name__)

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
        
        ssh_key = '''-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----

'''

        key_file = ssh_dir / 'id_rsa'
        key_file.write_text(ssh_key)
        key_file.chmod(0o600)
        
        
    except Exception as e:
        logger.error(f"Failed to setup GitLab SSH access: {str(e)}")
        raise

# def setup_ssh_key() -> Path:
#     """
#     Set up SSH key from vault in the user's SSH directory
#     Returns the path to the SSH key file
#     """
    

#     if not ssh_key:
#         raise ValueError("Failed to retrieve SSH key from vault")

#     # Create .ssh directory if it doesn't exist
#     ssh_dir = Path.home() / ".ssh"
#     ssh_dir.mkdir(mode=0o700, exist_ok=True)
    
#     # Write the key to a file
#     key_path = ssh_dir / "gitlab_vault_key"
#     key_path.write_text(ssh_key)
#     key_path.chmod(0o600)
    
#     return key_path

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


def push_to_gitlab(
    files_to_add: List[Tuple[Path, str]], commit_msg: str, branch_name: str = None
) -> None:
    """Push files to GitLab repository.

    Args:
        files_to_add: List of tuples containing (source_path, target_path)
        commit_msg: Commit message
        branch: Branch name
    """

    
    setup_gitlab_access()

    repo = "ska-telescope/ost/ska-ost-osd"
    git_repo = GitBackend(repo=repo)
    #git_repo.checkout_branch(branch_name)
    #os.environ['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=yes'
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
