import pandas as pd

from actuarygpt_workbench.utils.data_utils import standardize_columns


def test_standardize_columns_integer_headers():
    df = pd.DataFrame([[1, 2, 3]], columns=[2018, 2019, 2020])
    out = standardize_columns(df)
    assert list(out.columns) == ["2018", "2019", "2020"]


def test_standardize_columns_mixed_type_headers():
    df = pd.DataFrame([[1, 2, 3]], columns=["Origin", 2020, None])
    out = standardize_columns(df)
    assert list(out.columns) == ["origin", "2020", "none"]


def test_standardize_columns_deduplicates_after_lowercase():
    df = pd.DataFrame([[1, 2, 3, 4]], columns=["Origin", " origin ", "ORIGIN", 2020])
    out = standardize_columns(df)
    assert list(out.columns) == ["origin", "origin_1", "origin_2", "2020"]


def test_sample_loader_handles_non_string_columns(monkeypatch):
    import sys
    import types

    from actuarygpt_workbench.services.sample_data import load_sample

    class FakeTriangle:
        def to_frame(self, origin_as_datetime=False):
            return pd.DataFrame(
                {
                    0: ["2018", "2018", "2019"],
                    1: [0, 1, 0],
                    2: [100.0, 150.0, 120.0],
                }
            )

    fake_cl = types.SimpleNamespace(load_sample=lambda name: FakeTriangle())
    monkeypatch.setitem(sys.modules, "chainladder", fake_cl)

    out = load_sample("genins")
    assert list(out.columns) == ["origin", "development", "value"]
    assert len(out) == 3
