Publishing Data
---------------

.. contents::


Publishing tmdata
~~~~~~~~~~~~~~~~~

The tmdata is published to CAR with the same version as the Python package, so a
breaking change to the tmdata is released as a new major version. Consumers should
read a pinned version, ``car:ost/ska-ost-osd?<version>`` (e.g. ``?8.0.0``), rather
than ``main``.

It is published by the manual ``tmdata-publish`` job of the GitLab pipeline, which
runs:

.. code-block:: bash

    # Publish TMData to artifact repository
    make tmdata-publish

View TMData Releases
~~~~~~~~~~~~~~~~~~~~

To view current TMData releases: `TMData Releases <https://gitlab.com/ska-telescope/ost/ska-ost-osd/-/blob/main/tmdata/version_mapping/latest_release.txt?ref_type=heads>`_


Manual tmdata Release Steps
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create a JIRA issue and the branch

    1st: Create a new issue on the Release Management Jira Project with a summary of your release, and set it to “IN PROGRESS”.

    2nd: Create and checkout a new rel-XXX-release-v-1-2-2 branch (where REL-XXX is your Jira issue.)

2. Check the Current Version

.. code:: bash

    make show-version

3. Bump the Version

.. code:: bash

    make bump-patch-release

4. Set the Release

* `For remaining release steps click here <https://developer.skao.int/en/latest/tutorial/release-management/automate-release-process.html>`_

.. warning::

    This is a very crucial part for OSD, without this some functionality may break and exceptions and errors will be raised.
