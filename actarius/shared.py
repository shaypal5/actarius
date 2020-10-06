"""Shared code for actarius."""

import os
import sys
import json
import pickle
import shutil
import subprocess
from functools import lru_cache

import git
import mlflow

from .cfg import CFG


# MLflow setup
REMOTE_SERVER_URI = "databricks"  # set to your server URI
mlflow.set_tracking_uri(REMOTE_SERVER_URI)


ART_DNAME_TEMPLATE = "mlflow_artifacts_{}"

CACHE_DPATH = CFG.xdg_cache_dpath()
os.makedirs(CACHE_DPATH, exist_ok=True)


# === Artifact-related code ===

class ArgusArtifactory(object):

    def __init__(self, run_id, artifacts_dpath=None):
        self.run_id = run_id
        self.artifacts_dpath = artifacts_dpath
        if artifacts_dpath is None:
            self.artifacts_dpath = os.path.join(
                os.getcwd(), ART_DNAME_TEMPLATE.format(self.run_id))
        os.makedirs(self.artifacts_dpath, exist_ok=True)
        self._closed = False
        print("Artifact directory for current run: {}".format(
            self.artifacts_dpath))

    def log_artifacts(self, artifacts_dir_paths=None):
        """Logs all artifacts in all configured artifact directories to MLflow.

        Parameters
        ----------
        artifacts_dir_paths : str or list of str, optional
            If given, all artifacts in the given directory or directories are
            uploaded to the MLflow run tracking this run.
        """
        print("Logging artifacts for run {}...".format(self.run_id))
        print("Logging artifacts in {}...".format(self.artifacts_dpath))
        if self._closed:
            print(("ArgusArtifactory is alreaady closed! Artifacts logging "
                   "skipped!."))
        mlflow.log_artifacts(self.artifacts_dpath)
        if artifacts_dir_paths is not None:
            if isinstance(artifacts_dir_paths, str):
                print("Logging artifacts in {}...".format(artifacts_dir_paths))
                mlflow.log_artifacts(artifacts_dir_paths)
            else:
                for path in artifacts_dir_paths:
                    print("Logging artifacts in {}...".format(path))
                    mlflow.log_artifacts(path)
        print("Done logging artifacts.")

    def close(self):
        """Destorys temporary resources this artifactory uses."""
        self._closed = True
        shutil.rmtree(self.artifacts_dpath)


def log_df(df, name):
    """Logs the input dataframe with the given name in the running experiment.

    The dataframe is saved as a csv file.

    Parameters
    ==========
    df : pandas.DataFrame
        The dataframe to save as an experiment artifact.
    name : str
        The name to assign to the saved artifact.
    """
    fpath = os.path.join(CACHE_DPATH, name)
    df.to_csv(fpath)
    mlflow.log_artifact(fpath)
    os.remove(fpath)


def log_obj(obj, name):
    """Logs the input object with the given name in the running experiment.

    Pickles the input Python object.

    Parameters
    ==========
    obj : object
        A Python object to pickle.
    name : str
        The name to assign to the saved artifact.
    """
    fpath = os.path.join(CACHE_DPATH, name)
    with open(fpath, 'wb+') as f:
        pickle.dump(obj, f)
    mlflow.log_artifact(fpath)
    os.remove(fpath)


def log_obj_as_text(obj, name):
    """Logs the input object with the given name in the running experiment.

    Prints the string represention of the object into a text file.

    Parameters
    ==========
    obj : object
        A Python object to write a string represention of to file.
    name : str
        The name to assign to the saved artifact.
    """
    fpath = os.path.join(CACHE_DPATH, name)
    with open(fpath, 'wt+') as f:
        f.write(str(obj))
    mlflow.log_artifact(fpath)
    os.remove(fpath)


# === Logging-related code ===

class Logger(object):
    def __init__(self, stream, log_file):
        self.stream = stream
        self.log_file = log_file

    def write(self, message):
        self.log_file.write(message)
        self.stream.write(message)

    def __getattr__(self, attr):
        return getattr(self.stream, attr)

    def close(self):
        pass

    def flush(self):
        self.log_file.flush()
        self.stream.flush()


class DoubleLogger(object):
    def __init__(self, log_fpath):
        self.prev_stdout = sys.stdout
        self.prev_stderr = sys.stderr
        self.log_file = open(log_fpath, "a")
        # init stdout logging
        self.stdout_logger = Logger(self.prev_stdout, self.log_file)
        sys.stdout = self.stdout_logger
        # init stderr logging
        self.stderr_logger = Logger(self.prev_stderr, self.log_file)
        sys.stderr = self.stderr_logger

    def close(self):
        self.log_file.close()
        sys.stdout = self.prev_stdout
        sys.stderr = self.prev_stderr


# === git-related tags ===

@lru_cache(maxsize=1)
def _git_repo():
    return git.Repo(os.getcwd(), search_parent_directories=True)


@lru_cache(maxsize=1)
def _git_conf_reader():
    return _git_repo().config_reader()


# @lru_cache(maxsize=1)
# def git_username():
#     _git_conf_reader().get_value("user", "name")


# @lru_cache(maxsize=1)
# def git_user_email():
#     _git_conf_reader().get_value("user", "email")


@lru_cache(maxsize=1)
def git_repo_name():
    try:
        url = _git_repo().remotes.origin.url
        if '/' in url:
            url = url.split('/')[-1]
        if url.endswith('.git'):
            url = url[:-4]  # remove .git from end of url
        return url
    except git.exc.InvalidGitRepositoryError:
        return "NotFromGitRepo"


@lru_cache(maxsize=1)
def git_branch():
    try:
        return _git_repo().active_branch.name
    except (git.exc.InvalidGitRepositoryError, TypeError):
        return "NotFromGitRepo"


def _minimal_ext_cmd(cmd):
    # construct minimal environment
    env = {}
    for k in ['SYSTEMROOT', 'PATH', 'HOME']:
        v = os.environ.get(k)
        if v is not None:
            env[k] = v
    # LANGUAGE is used on win32
    env['LANGUAGE'] = 'C'
    env['LANG'] = 'C'
    env['LC_ALL'] = 'C'
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
    return out


def _safe_cmd_res(cmd_arry, unknown_str="UnknownValue"):
    try:
        out = _minimal_ext_cmd(cmd_arry)
        res = out.strip().decode('ascii')
    except (subprocess.SubprocessError, OSError):
        return unknown_str
    if not res:
        # this shouldn't happen but apparently can (see gh-8512)
        return unknown_str
    return res


@lru_cache(maxsize=1)
def git_commit_checksum():
    return _safe_cmd_res(
        cmd_arry=['git', 'rev-parse', 'HEAD'],
        unknown_str="NotFromGitRepo",
    )


@lru_cache(maxsize=1)
def git_username():
    return _safe_cmd_res(['git', 'config', 'user.name'])


@lru_cache(maxsize=1)
def git_user_email():
    return _safe_cmd_res(['git', 'config', 'user.email'])


@lru_cache(maxsize=1)
def sagemaker_instance_name():
    log_path = '/opt/ml/metadata/resource-metadata.json'
    try:
        with open(log_path, 'r') as logs:
            _logs = json.load(logs)
        return _logs['ResourceName']
    except FileNotFoundError:
        return "NotFromSageMaker"


def set_shared_tags():
    mlflow.set_tag('git_repo', git_repo_name())
    mlflow.set_tag('git_branch', git_branch())
    mlflow.set_tag('git_username', git_username())
    mlflow.set_tag('git_user_email', git_user_email())
    mlflow.set_tag('git_commit_checksum', git_commit_checksum())
    mlflow.set_tag('sagemaker_instance_name', sagemaker_instance_name())
