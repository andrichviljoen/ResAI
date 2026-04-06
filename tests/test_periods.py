import pandas as pd

from actuarygpt_workbench.utils.periods import parse_period_label, period_distance


def test_parse_period_label_formats():
    assert parse_period_label("2018").year == 2018
    assert parse_period_label("201801").month == 1
    assert parse_period_label("2018Q2").quarter == 2
    assert parse_period_label("2018-01-01").month == 1


def test_period_distance_annual_and_quarterly():
    o = pd.Period("2018-01", freq="M")
    v = pd.Period("2020-01", freq="M")
    assert period_distance(o, v, "annual") == 2
    assert period_distance(o, v, "quarterly") == 8
