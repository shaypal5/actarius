"""MLflow experiment run handles."""

import os
import time
import random
import pickle
import warnings
import traceback

import mlflow
from mlflow.exceptions import MlflowException
try:
    from databricks_cli.utils import InvalidConfigurationError as DatabricksInvalidConfigurationError  # noqa: E501
except ImportError:
    from .exceptions import MockDatabricksInvalidConfigurationError as DatabricksInvalidConfigurationError  # noqa: E501

from .shared import (
    ArgusArtifactory,
    DoubleLogger,
    set_shared_tags,
)
from .cfg import (
    TEMP_DIR,
    PRINT_STACKTRACE,
)


class ExperimentRun(object):
    """A class representing a run of an MLflow experiment.

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
        self.temp_run_id = random.randint(1, 999999)
        self.log_fpath = os.path.expanduser(
            f'{TEMP_DIR}/log_mlflow_run_{self.temp_run_id}.txt')
        os.makedirs(os.path.expanduser('~/temp'), exist_ok=True)
        self.logger = DoubleLogger(self.log_fpath)
        self.artifactory = ArgusArtifactory(
            run_id=self.temp_run_id,
            artifacts_dpath=artifacts_dpath,
        )
        self.artifact_dpath = self.artifactory.artifacts_dpath
        self.start_time = time.time()
        self.running = True
        self.tags = {}
        self.params = {}
        self.metrics = {}
        self.disabled = False

    def set_tag(self, name, val):
        self.tags[name] = val

    def set_tags(self, tag_dict):
        self.tags = {**self.tags, **tag_dict}

    def log_param(self, name, val):
        self.params[name] = val

    def log_params(self, param_dict):
        self.params = {**self.params, **param_dict}

    def log_metric(self, name, val):
        self.metrics[name] = val

    def log_metrics(self, metric_dict):
        self.metrics = {**self.metrics, **metric_dict}

    def log_df(self, df, name):
        fpath = os.path.join(self.artifact_dpath, name)
        df.to_csv(fpath)

    def log_obj(self, obj, name):
        """Logs the input object with the given name in the running experiment.

        Pickles the input Python object.

        Parameters
        ==========
        obj : object
            A Python object to pickle.
        name : str
            The name to assign to the saved artifact.
        """
        fpath = os.path.join(self.artifact_dpath, name)
        with open(fpath, 'wb+') as f:
            pickle.dump(obj, f)

    def log_obj_as_text(self, obj, name):
        """Logs the input object with the given name in the running experiment.

        Prints the string represention of the object into a text file.

        Parameters
        ==========
        obj : object
            A Python object to write a string represention of to file.
        name : str
            The name to assign to the saved artifact.
        """
        fpath = os.path.join(self.artifact_dpath, name)
        with open(fpath, 'wt+') as f:
            f.write(str(obj))

    def end_run(
            self, tags=None, params=None, metrics=None,
            artifacts_dir_paths=None):
        """Ends the currently running experiment and reports to MLflow.

        Parameters
        ----------
        tags : dict, optional
            Dictionary of tag_name: String -> value: (String, but will be
            string-ified if not).
        params : dict, optional
            Dictionary of param_name: String -> value: (String, but will be
            string-ified if not).
        metrics : dict, optional
            Dictionary of metric_name: String -> value: Float. Note that some
            special values such as +/- Infinity may be replaced by other values
            depending on the store. For example, sql based store may replace
            +/- Inf with max / min float values.
        artifacts_dir_paths : str or list of str, optional
            If given, all artifacts in the given directory or directories are
            uploaded to the MLflow run tracking this run.
        """
        # init mlflow run
        runtime = time.time() - self.start_time
        try:
            mlflow.set_experiment(experiment_name=self.experiment_name)
        except (MlflowException, DatabricksInvalidConfigurationError):
            warnings.warn(
                "MLflow was badly configured! Argus was disabled for the run.",
                stacklevel=2
            )
            if PRINT_STACKTRACE:
                warnings.warn(
                    "Printing exception stack trace and contining to run.",
                    stacklevel=2,
                )
                traceback.print_stack()
            self.disabled = True
            self.running = False
            self.artifactory.close()
            self.logger.close()
            try:
                mlflow.end_run()
            except Exception:
                # this is meant to kill stupid mlflow errors on program end,
                # as it seems they register end_run() to be called on program
                # end using atexit._run_exitfuncs
                pass
            return
        with mlflow.start_run(
            run_name=self.run_name,
            nested=self.nested,
        ) as run:
            self.run_id = run.info.run_id
            set_shared_tags()
            mlflow.set_tags(self.tags)
            if tags:
                mlflow.set_tags(tags)

            # log all params
            mlflow.log_params(self.params)
            if params:
                mlflow.log_params(params)

            # log metrics
            mlflow.log_metrics(self.metrics)
            mlflow.log_metrics({
                'runtime_in_sec': runtime
            })
            if metrics:
                mlflow.log_metrics(metrics)
            self.artifactory.log_artifacts(
                artifacts_dir_paths=artifacts_dir_paths)
            self.artifactory.close()
            self.logger.close()
            mlflow.log_artifact(local_path=self.log_fpath)
            os.remove(self.log_fpath)
        self.running = False
