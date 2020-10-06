"""Testing the actarius package."""

import time
from random import (
    random,
    randint,
)

import pandas as pd

from actarius import ExperimentRun

from .shared import CustomClass


TEST_EXP_PATH = "/Shared/Tests/actarius_test_basic"


def test_experiment_obj():
    exp = ExperimentRun(TEST_EXP_PATH)
    exp.set_tags({
        'test': 'exp_obj',
        'key': 'value',
    })

    # log params
    a = randint(0, 4)
    b = randint(0, 100)
    c = random()
    exp.log_param("a", a)
    exp.log_param("b", b)
    exp.log_param("c", c)

    # read the data
    print("Timing some action...")
    start = time.time()
    sumi = 0
    for i in range(randint(0, 9999)):
        sumi = (sumi + 1) * 1.2
    end = time.time()
    exp.log_metric("some_action_time_sec", end - start)
    print("Some action took {} seconds".format(end - start))

    print("Now logging a dataframe...")
    df = pd.DataFrame(
        data=[[1, 2, 'a'], [2, 4, 'b']],
        index=[1, 2],
        columns=['num1', 'num2', 'char']
    )
    exp.log_df(df, 'some_dataframe.csv')
    print("Logged a dataframe!")

    print("Now logging some custom object...")
    custi = CustomClass(a=3, b=88)
    exp.log_obj(custi, 'custom_obj.pkl')
    print("Logged a custom object!")

    print("Now logging list as a text file...")
    exp.log_obj_as_text([1, 3, 5], 'int_list.txt')
    print("Logged an int list as a text file!")

    exp.log_metric("sum", a + b)
    exp.end_run()
