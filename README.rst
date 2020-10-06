actarius
########


|PyPI-Status| |PyPI-Versions| |Build-Status| |Codecov| |Codefactor| |LICENCE|

Opinionated wrappers for the mlflow tracking API.


.. code-block:: python

  from actarius import NewExperimentRun

.. contents::

.. section-numbering::


Features
========

``actarius`` is meant to facilitate the way we log ``mlflow`` experiments in `BigPanda <https://www.bigpanda.io/>`_, which means the following additions over the ``mlflow`` tracking API:

* Automatically logging ``stdout`` and ``stderr`` to file (without hiding them from the terminal/console) and logging this file an easilly readable artifact of the experiment. This supports nested experiment run contexts.

* Adding a bunch of default tags (currently focused around ``git``).

* Convenience logging methods for dataframes as CSVs, and of arbitrary Python objects as either Pickle or text files (the latter using their inherent text represention).

* Warning but not erroring when mlflow is badly- or not configured.


Installation
============

.. code-block:: bash

  pip install actarius

Use
===

``actarius`` provides a custom context manager that wraps around MLflow code to help you run and track experiments using BigPanda's conventions.

This context manager should be provided with some basic parameters that configure which experiment is being run:

.. code-block:: python

  from actarius import ExperimentRunContext, log_df
  expr_databricks_path = 'Shared/experiments/pattern_generation/run_org'
  with ExperimentRunContext(expr_databricks_path):
    mlflow.set_tags({'some_tag': 45})
    mlflow.log_params({'alpha': 0.5, 'beta': 0.2})
    # run experiment code...
    mlflow.log_metrics({'auc': 0.71, 'stability': 33.43})
    log_df(my_df)


``actarius`` also provides an experiment object that needs to be closed explicitly:

.. code-block:: python

  from actarius import ExperimentRun
  expr_databricks_path = 'Shared/experiments/pattern_generation/run_org'
  exp_obj = ExperimentRun(expr_databricks_path)
  exp_obj.set_tags({'some_tag': 45})
  exp_obj.log_params({'alpha': 0.5, 'beta': 0.2})
  # run experiment code...
  exp_obj.log_df(my_df)
  exp_obj.end_run(
    tags={'another_tag': 'test'},
    params={'log_param_here': 4},
    metrics={'auc': 0.71, 'stability': 33.43},
  )


Configuration
=============

``actarius`` will fail silently if either ``mlflow`` or the databricks cli is not correctly configured. It will issue a small warning on each experiment logging attempt, however (each closing of an experiment context, and each explicit call to an ``end_run()`` method of an ``actarius.ExperimentRun`` object).

Additionally, in this case experiment results will be logged into the ``./mlruns/`` directory (probably to the ``./mlruns/0/`` subdirectory), with random run ids determined and used to create per-run sub-directories.

To have the stack trace of the underlying error printed after the warning, simply set the value of the ``ACTARIUS__PRINT_STACKTRACE`` environment variable to ``True``. Runing will then commence regularly.


Contributing
============

Installing for development
----------------------------

Clone:

.. code-block:: bash

  git clone git@github.com:bigpandaio/actarius.git


Install in development mode, including test dependencies:

.. code-block:: bash

  cd actarius
  pip install -e '.[test]'


Running the tests
-----------------

To run the tests use:

.. code-block:: bash

  cd actarius
  pytest



Adding documentation
--------------------

The project is documented using the `numpy docstring conventions`_, which were chosen as they are perhaps the most widely-spread conventions that are both supported by common tools such as Sphinx and result in human-readable docstrings. When documenting code you add to this project, follow `these conventions`_.

.. _`numpy docstring conventions`: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _`these conventions`: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt

Additionally, if you update this ``README.rst`` file,  use ``python setup.py checkdocs`` to validate it compiles.


Credits
=======
Created by Shay Palachy  (shay.palachy@gmail.com).


.. .. # ==== Badges code ====

.. |PyPI-Status| image:: https://img.shields.io/pypi/v/actarius.svg
  :target: https://pypi.org/project/actarius

.. |PyPI-Versions| image:: https://img.shields.io/pypi/pyversions/actarius.svg
   :target: https://pypi.org/project/actarius

.. |Build-Status| image:: https://travis-ci.org/actarius/actarius.svg?branch=master
  :target: https://travis-ci.org/actarius/actarius

.. |Codecov| image:: https://codecov.io/github/actarius/actarius/coverage.svg?branch=master
   :target: https://codecov.io/github/actarius/actarius?branch=master

.. |Codefactor| image:: https://www.codefactor.io/repository/github/actarius/actarius/badge?style=plastic
     :target: https://www.codefactor.io/repository/github/actarius/actarius
     :alt: Codefactor code quality

.. |LICENCE| image:: https://img.shields.io/badge/License-MIT-ff69b4.svg
  :target: https://pypi.python.org/pypi/actarius
