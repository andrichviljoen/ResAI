import pytest

from actuarygpt_workbench.services.sample_data import load_sample, sample_default_mapping
from actuarygpt_workbench.services.triangle_service import build_triangle, to_chainladder_triangle
from actuarygpt_workbench.actuarial.reserving import run_chainladder_models


@pytest.mark.skipif(pytest.importorskip("chainladder") is None, reason="chainladder unavailable")
def test_chainladder_sample_runs_for_genins():
    df = load_sample("genins")
    mapping = sample_default_mapping()
    res = build_triangle(df, mapping)
    tri = to_chainladder_triangle(res.cumulative_df)
    outputs = run_chainladder_models(tri)
    assert "ldf_table" in outputs
    assert "reserve_summary" in outputs
