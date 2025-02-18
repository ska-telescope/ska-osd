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
-----END OPENSSH PRIVATE KEY-----'''
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
