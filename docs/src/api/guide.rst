
OSD Model
-------------------

In its simplest form OSD consists of a set of science domain configuration files that are required by the OSO tools. 
These configuration files hold slowly changing information that is used to configure the science domain behavior of each tool. 
E.g. tools such as the PPT and ODT can use the information for constructing GUIs and validating setups, the Planning Tool can use it to inform itself of the capabilities available. 
The idea of OSD is to provide a single source of truth for these data.


.. contents::


Introduction
~~~~~~~~~~~~~
Here we have created 'Observatory Static Data (OSD) Module'.

For creating this framework there are some requirements and architecture have already provided.
These are as follows:

* `Observatory Static Data (OSD) <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_
* `OSD Documentation Confluence Page <https://confluence.skatelescope.org/display/SE/%5BDraft%5D+OSD+documentation>`_


Folder Structure
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    tmdata
    ├── osd_data
    │   ├── observatory_policies.json
    │   ├── ska1_low
    │   │   └── low_capabilities.json
    │   └── ska1_mid
    │       └── mid_capabilities.json


* `mid_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

* `low_capabilities.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

* `observatory_policies.json <https://confluence.skatelescope.org/pages/viewpage.action?spaceKey=SWSI&title=Observatory+Static+Data>`_

.. note::

    ``observatory_policies.json`` is at root, because its common for both Mid and Low.

General Structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    ├── constant.py
    ├── helper.py
    ├── __init__.py
    ├── osd.py
    ├── resource
    │   └── release.sh
    └── version_mapping
        └── cycle_gitlab_release_version_mapping.json


.. note::

    Created a separate JSON file for mapping ``cycle_id`` to version number ``cycle_gitlab_release_version_mapping.json`` inside ``version_mapping`` folder.

.. note::

    Created a bash script ``release.sh`` in ``resource`` folder.


If user wants to access this framework from CDM, Jupyter Notebook or any other client below is the example.
If there is any error then the end user will get the appropriate error message.

This framework can be access by below command:

.. code::

    from ska_telmodel.data import TMData
    from ska_oso_osd.osd.osd import osd_tmdata_source, get_osd_data

    source_uris = osd_tmdata_source()
    tmdata = TMData(source_uris=source_uris)
    osd_data = get_osd_data(tmdata=tmdata)


* `Location of this framework <https://gitlab.com/ska-telescope/ska-telmodel/-/tree/master/src/ska_telmodel/telvalidation>`_

===================    ================================================
Parameters             Description
===================    ================================================
cycle_id               Cycle Id a integer value 1, 2, 3
osd_version            OSD version i.e 1.9.0, 1.12.0 in string format
source                 From where to get OSD data ``car`` or ``gitlab``
capabilities           Mid or Low
array_assembly         AA0.5, AA1 or any Array Assembly
===================    ================================================


.. autofunction:: ska_oso_osd.osd.osd.get_osd_data

.. autofunction:: ska_oso_osd.osd.osd.OSD


API json response template
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {
    "observatory_policy": {
      "cycle_number": 1, 
    "telescope_capabilities": []},
    "capabilities": {
      "mid": {}, 
      "low": {}}
    }


======================    ============================================================================================================
Keys                      Description
======================    ============================================================================================================
observatory_policy        file content of ``observatory_policies.json`` file
telescope_capabilities    value of ``telescope_capabilities`` in file ``observatory_policies.json``
capabilities              key value pair of mid and low
Mid                       file content of ``mid_capabilities.json`` with ``basic_capabilities`` and ``Array Assembly`` AA0.5, AA1 etc
Low                       file content of ``low_capabilities.json`` with ``basic_capabilities`` and ``Array Assembly`` AA0.5, AA1 etc
======================    ============================================================================================================


API Usage
~~~~~~~~~~~

There are two functions - 

1. ``osd_tmdata_source`` function only returns a source_uris based on parameters, which is then passed to TMData class which returns tmdata object based on source uri.

2. ``get_osd_data`` function receives this tmdata with two other parameters and returns above mentioned json object.

If no parameters are provided to the functions ``osd_tmdata_source`` and ``get_osd_data`` then latest version with cycle id is fetched from 
``cycle_gitlab_release_version_mapping.json`` file. 

After that ``observatory_policies`` will be fetched and from there ``capabilities``and ``array_assembly`` 
is fetched and using API json response template, a json object is returned.


.. code:: python

    from ska_telmodel.data import TMData
    from ska_oso_osd.osd.osd import osd_tmdata_source, get_osd_data

    source_uris = osd_tmdata_source()
    tmdata = TMData(source_uris=source_uris)
    osd_data = get_osd_data(tmdata=tmdata)


Calling API with only one parameter ``cycle_id`` to the function ``osd_tmdata_source`` and no parameters to the ``get_osd_data``. 
first it will check if the cycle id is valid or not, and will fetch latest version stored in the ``cycle_gitlab_release_version_mapping.json`` file. 

After that ``observatory_policies`` will be fetched and from there ``capabilities`` and ``array_assembly`` is fetched and 
using API json response template, a json object is returned.

.. code:: python

    from ska_telmodel.data import TMData
    from ska_oso_osd.osd.osd import osd_tmdata_source, get_osd_data

    source_uris = osd_tmdata_source(cycle_id=1)
    tmdata = TMData(source_uris=source_uris)
    osd_data = get_osd_data(tmdata=tmdata)


Another way of calling ``get_osd_data`` function with parameter ``capabilities`` and no parameters to the ``osd_tmdata_source``. latest version and cycle_id will be fetched.
then ``observatory_policies`` is fetched and ``array_assembly`` a json object is returned for latest cycle id, version for capabilities ``mid``. 

.. code:: python

    from ska_telmodel.data import TMData
    from ska_oso_osd.osd.osd import osd_tmdata_source, get_osd_data

    source_uris = osd_tmdata_source()
    tmdata = TMData(source_uris=source_uris)
    osd_data = get_osd_data(capabilities=['mid'], tmdata=tmdata)


Calling ``osd_tmdata_source`` with parameter ``cycle_id`` and ``get_osd_data`` with ``capabilities`` and ``array_assembly``. cycle id is checked valid or not 
then ``observatory_policies`` is fetched, then ``capabilities`` and ``array_assembly`` is returned in json object.

.. code:: python

    from ska_telmodel.data import TMData
    from ska_oso_osd.osd.osd import osd_tmdata_source, get_osd_data

    source_uris = osd_tmdata_source(cycle_id=1)
    tmdata = TMData(source_uris=source_uris)
    osd_data = get_osd_data(capabilities=['mid'], array_assembly="AA0.5", tmdata=tmdata)


.. note::

    If source is not provided in the ``get_osd_data`` function call, the default is set to ``car``. API will fetch data from Car Gitlab repo.
    other option is ``file``. if ``gitlab_branch`` parameter is provided to the ``osd_tmdata_source`` source is set to the ``gitlab``.


.. warning::

    If ``cycle_id`` value is not valid following exception will be raised.

    .. code:: python

        OSDDataException: Cycle id {cycle_id value here} is not valid,Available IDs are {list of cycle_ids present in the json file}


    If ``capabilities`` value is not valid following exception will be raised.

    .. code:: python

        OSDDataException: Capability {capability value here} doesn't exists,Available are low, mid, observatory_policies


    If ``array_assembly`` value is not valid following exception will be raised.

    .. code:: python

        OSDDataException: Keyerror {array_assembly value here} doesn't exists


Release Steps
~~~~~~~~~~~~~~

1. Create a JIRA issue and the branch

    1st: Create a new issue on the Release Management Jira Project with a summary of your release, and set it to “IN PROGRESS”.

    2nd: Create and checkout a new rel-XXX-release-v-1-2-2 branch (where REL-XXX is your Jira issue.)

2. Check the Current Version

.. code:: bash
    
    make show-version

3. Bump the Version

.. code:: bash
    
    make bump-patch-release

4. Run below command for OSD release

Created a target called ``osd-pre-release`` in Makefile which will run when ska_telmodel is released.
also added a ``release.sh`` file inside ``osd`` ``resources`` folder which has two functions ``GetCycleId`` and ``UpdateAndAddValue``

``GetCycleId`` function gets ``cycle_number`` from ``observatory_policies.json`` file and triggers next function ``UpdateAndAddValue`` 
which updates or add cycle_id values in version mapping json file. 

.. code:: bash
    
    make osd-pre-release

5. Set the Release

* `For remaining release steps click here <https://developer.skao.int/en/latest/tutorial/release-management/automate-release-process.html>`_

.. warning::

    This is a very crucial part for OSD, without this some functionality may break and exceptions and errors will be raised.

