Publishing Data
---------------

.. contents::

Files in the ``tmdata`` directory of ``main`` are published to the Central
Artefact Repository (CAR), where consumers read them using the URI
``car:ost/ska-ost-osd?main``. A change is served as soon as it is published:
publishing doesn't need a release of the library, and releasing the library
doesn't publish the tmdata.


Changing the data
~~~~~~~~~~~~~~~~~

1. Change the files in ``tmdata`` in a merge request to ``main``. Its pipeline
   validates them.
2. Once it is merged, run the manual ``tmdata-publish`` job in the ``main``
   pipeline.


The publish job
~~~~~~~~~~~~~~~

The ``tmdata-publish`` job:

* Runs only in pipelines for ``main``. Tags are for releases of the library, and
  merge request and other branch pipelines must not publish data.
* Is manual, so the data is published when someone chooses to, not on every merge
  to ``main``.
* Needs ``tmdata-validate`` to pass. It validates the tmdata with
  ``osd-validate-tmdata`` from a release of ska-ost-osd, set by
  ``OSD_VALIDATOR_VERSION`` in the ``Makefile``, rather than the code in the
  repository, so the data is checked by the library that deployments read it
  with. To change the file schema, release and deploy the library first, then
  update ``OSD_VALIDATOR_VERSION``, then change the data.
* Publishes only if the tmdata differs from what the CAR serves for ``main``, so
  running it again doesn't publish the same data twice.
* Checks afterwards that the CAR serves the tmdata. ``make tmdata-publish`` exits
  successfully even when the CAR rejects the upload, so this check is what fails
  the job. If it fails, retry it in the latest ``main`` pipeline.


Stale publishes
~~~~~~~~~~~~~~~

If publish jobs from two pipelines run close together, the earlier pipeline could
publish after the later one, and the CAR would serve older data than ``main``
holds. The job prevents this with:

* A resource group, ``tmdata-main``, so only one publish job runs at a time.
* An environment, ``tmdata/main``, which records the pipeline whose publish job
  last succeeded. With "Prevent outdated deployment jobs" on, GitLab refuses a publish
  job from an earlier pipeline.

These rely on two project settings, in Settings → CI/CD → General pipelines:

* **Prevent outdated deployment jobs**: on.
* **Allow job retries for rollback deployments**: off. Retrying an old publish job
  would publish older data than ``main`` holds.


Rolling back
~~~~~~~~~~~~

To go back to earlier data, revert the change in a merge request and publish it,
so that ``main`` and what the CAR serves always agree.


Clients before 8.0.0
~~~~~~~~~~~~~~~~~~~~

Releases of ska-ost-osd before 8.0.0 read ``tmdata/version_mapping`` on ``main`` to
find the release whose tmdata to read, as described in :ref:`legacy-publishing`.
Leave the files in ``tmdata/version_mapping`` as they are.
