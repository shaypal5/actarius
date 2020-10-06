"""MLflow-integrated context managers for BigPanda."""

import os
import time
# import atexit
import warnings
import traceback

import mlflow
from mlflow.exceptions import MlflowException
# from mlflow.tracking.fluent import end_run as fluent_end_run
from databricks_cli.utils import InvalidConfigurationError

from .shared import (
    ArgusArtifactory,
    DoubleLogger,
    set_shared_tags,
)
from .cfg import (
    TEMP_DIR,
    PRINT_STACKTRACE,
)


class ExperimentRunContext(object):
    """A context manager for running experiments.

    Parameters
    ----------
    experiment_name : str
        Name of experiment to be activated. In case of a databricks experiment,
        this is the full path to the databricks experiment used to track
        experiment results.
    run_name : str, optional
        Name of new run (stored as a mlflow.runName tag). Used only when run_id
        is unspecified.
    nested : bool, default False
        Controls whether run is nested in parent run. True creates a nest run.
    artifacts_dpath : str, optional
        The path to the local filesystem directory where experiment artifacts
        will be saved. If not given, a default one is created.
    """

    def __init__(
            self, experiment_name, run_name=None, nested=False,
            artifacts_dpath=None
    ):
        self.experiment_name = experiment_name
        self.run_name = run_name
        self.nested = nested
        self.disabled = False
        # Note: on Databricks, the experiment name passed to
        # mlflow_set_experiment must be a valid path in the workspace
        try:
            mlflow.set_experiment(self.experiment_name)
        except (MlflowException, InvalidConfigurationError):
            warnings.warn(
                "MLflow is badly configured! Argus is disabled.",
                stacklevel=2,
            )
            if PRINT_STACKTRACE:
                warnings.warn(
                    "Printing exception stack trace and contining to run.",
                    stacklevel=2,
                )
                traceback.print_stack()
            # was not needed, eventually, but keeping this here
            # atexit.unregister(mlflow.end_run)
            # atexit.unregister(fluent_end_run)
            self.disabled = True
            try:
                mlflow.end_run()
            except Exception:
                # this is meant to kill stupid mlflow errors on program end,
                # as it seems they register end_run() to be called on program
                # end using atexit._run_exitfuncs
                pass
            return
        self.mlflow_run = mlflow.start_run()
        self.run_id = self.mlflow_run .info.run_id
        self.log_fpath = f'{TEMP_DIR}/log_mlflow_run_{self.run_id}.txt'
        os.makedirs(os.path.expanduser('~/temp'), exist_ok=True)
        self.logger = DoubleLogger(self.log_fpath)
        self.artifactory = ArgusArtifactory(
            run_id=self.run_id,
            artifacts_dpath=artifacts_dpath,
        )

    def __enter__(self):
        if self.disabled:
            # this make sure that all mlflow calls inside this context will
            # not throw exceptions, but instead will log runs into some file in
            # the default location - ./mlruns
            self._archived_tracking_uri = mlflow.get_tracking_uri()
            mlflow.set_tracking_uri('')
            return
        self.mlflow_run.__enter__()
        self.start_time = time.time()
        # print("git version: {}".format(git_version()))
        set_shared_tags()

    def __exit__(self, *args):
        if self.disabled:
            mlflow.set_tracking_uri(self._archived_tracking_uri)
            try:
                mlflow.end_run()
            except Exception:
                # this is meant to kill stupid mlflow errors on program end,
                # as it seems they register end_run() to be called on program
                # end using atexit._run_exitfuncs
                pass
            return
        runtime = time.time() - self.start_time
        mlflow.log_metrics({
            'runtime_in_sec': runtime
        })
        self.artifactory.log_artifacts(artifacts_dir_paths=None)
        self.artifactory.close()
        self.logger.close()
        mlflow.log_artifact(local_path=self.log_fpath)
        self.mlflow_run.__exit__(*args)
        os.remove(self.log_fpath)
