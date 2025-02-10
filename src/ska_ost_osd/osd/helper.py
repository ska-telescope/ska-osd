import json

import logging
import os
import sys

from pathlib import Path
from typing import Any

from ska_telmodel.data.new_data_backend import GitBackend

logging.basicConfig(level=logging.INFO)


def read_json(json_file_location: str) -> dict[dict[str, Any]]:
    """This function returns json file object from local file system

    :param json_file_location: json file.

    :returns: file content as json object
    """

    cwd = Path(__file__).resolve().parent.parent.parent.parent
    path = os.path.join(cwd, json_file_location)
    with open(path) as user_file:  # pylint: disable=W1514
        file_contents = json.load(user_file)

    return file_contents



# ################################################################################
# # Config
# repo = "ska-telescope/ost/ska-ost-osd"
# commit_title = "Commit new data"
# branch_name = "branch-name"
# ################################################################################


# print("Repo init...")
# git_repo = GitBackend(repo=repo)

# files_to_add_small = [
#     (
#         Path("/home/dayanand/ska/ska-ost-osd/tmdata/ska1_mid/mid_capabilities.json"),
#         "ska1_mid/mid_capabilities.json",
#     ),
# ]
# print("Create branch...")
# try:
#     git_repo.start_transaction(branch_name, create_new_branch=False)
# except ValueError as err:
#     if str(err) == "Branch Already Exists":
#         print("Branch already exists, try a different branch name")
#         sys.exit(1)
#     else:
#         raise

# print("Add small files...")
# for file, key in files_to_add_small:
#     print(f"Adding...{file}")
#     git_repo.add_data(file, key)

# print("Commit...")
# git_repo.commit(commit_title)

# print("Push Branch...")
# git_repo.commit_transaction()
