Introduction
------------

In its simplest form OSD consists of a set of science domain configuration files that are required by the OSO tools.
These configuration files hold slowly changing information that is used to configure the science domain behavior of each tool.
E.g. tools such as the PPT and ODT can use the information for constructing GUIs and validating setups, the Planning Tool can use it to inform itself of the capabilities available.
The idea of OSD is to provide a single source of truth for these data.


The OSD's requirements and architecture are described on Confluence:

* `Observatory Static Data (OSD) <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_
* `OSD Documentation Confluence Page <https://confluence.skatelescope.org/display/SE/%5BDraft%5D+OSD+documentation>`_


Installation
~~~~~~~~~~~~

Add the following entry under the ``[project]`` ``dependencies`` list in your ``pyproject.toml``:

.. code-block:: toml

    [project]
    dependencies = [
        "ska-ost-osd>=<majorversion>,<<nextmajorversion>",
    ]

This will ensure that a compatible version of the ``ska-ost-osd`` package is installed.
