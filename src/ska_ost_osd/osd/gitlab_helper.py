"""GitLab helper functions for OSD."""
import os
from pathlib import Path
import logging
from typing import List, Tuple
import sys
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

def push_to_gitlab(files_to_add: List[Tuple[Path, str]], commit_msg: str, branch_name:str) -> None:
    """Push files to GitLab repository.
    
    Args:
        files_to_add: List of tuples containing (source_path, target_path)
        commit_msg: Commit message
        branch: Branch name
    """
    repo = "ska-telescope/ost/ska-ost-osd"
    git_repo = GitBackend(repo=repo)
    modified_files = []
    
    for src_path, target_path in files_to_add:
        if check_file_modified(src_path):
            modified_files.append((src_path, target_path))
        else:
            logger.info(f"Skipping unmodified file: {src_path}")
            
    if not modified_files:
        logger.info("No modified files to push")
        return
        
    # Add files
    for src_path, target_path in modified_files:
        git_repo.add_data(src_path, target_path)
        
    # Commit and push
    git_repo.commit(commit_msg)
    print("Push Branch...")
    git_repo.commit_transaction()