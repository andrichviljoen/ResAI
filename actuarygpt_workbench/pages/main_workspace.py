from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from actuarygpt_workbench.actuarial.diagnostics import generate_findings
from actuarygpt_workbench.actuarial.reserving import deterministic_link_ratios, run_chainladder_models
from actuarygpt_workbench.ai.copilot import build_ai_context, run_ai
from actuarygpt_workbench.services.data_service import infer_schema, read_uploaded_file, validate_mapping
from actuarygpt_workbench.services.export_service import build_audit_pack, df_to_csv_bytes, to_json_bytes
from actuarygpt_workbench.services.sample_data import list_samples, load_sample, sample_default_mapping
from actuarygpt_workbench.services.triangle_service import build_triangle, to_chainladder_triangle


def _reset_after_data_change():
    for key in [
        "triangle_result",
        "triangle_definition",
        "triangle_summary",
        "link_ratio_df",
        "diagnostics",
        "selected_factors",
        "user_overrides",
        "reserve_outputs",
        "ai_context",
        "ai_history",
    ]:
        st.session_state[key] = {} if key in {"triangle_definition", "triangle_summary", "selected_factors", "user_overrides", "reserve_outputs", "ai_context"} else [] if key in {"diagnostics", "ai_history"} else None


def _show_triangle(df: pd.DataFrame, title: str):
    st.subheader(title)
    st.dataframe(df.style.format("{:.2f}"), use_container_width=True)
    hm = px.imshow(df.fillna(0), text_auto=True, aspect="auto", color_continuous_scale="Blues", labels={"x": "Development Age", "y": "Origin"})
    st.plotly_chart(hm, use_container_width=True)


def render_workspace() -> None:
    st.title("ActuaryGPT Triangle Diagnostic Workbench")
    tabs = st.tabs(["Data Intake", "Triangle Builder", "Diagnostics", "Pattern Detection", "Reserve Impact", "AI Copilot", "Audit / Export"])

    with tabs[0]:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### Load Data")
            choice = st.radio("Source", ["Sample dataset", "Upload file"], horizontal=True)
            if choice == "Sample dataset":
                sample = st.selectbox("Choose sample", list_samples())
                if st.button("Load sample"):
                    df = load_sample(sample)
                    st.session_state.raw_df = df
                    st.session_state.dataset_info = {"source": "sample", "name": sample, "rows": len(df)}
                    st.session_state.mapping = sample_default_mapping()
                    _reset_after_data_change()
            else:
                up = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx", "xls"])
                if up is not None:
                    try:
                        df = read_uploaded_file(up)
                        st.session_state.raw_df = df
                        st.session_state.dataset_info = {"source": "upload", "name": up.name, "rows": len(df)}
                        _reset_after_data_change()
                    except Exception as exc:
                        st.error(str(exc))

        with col2:
            if st.session_state.raw_df is not None:
                st.markdown("### Preview + Mapping")
                df = st.session_state.raw_df
                st.dataframe(df.head(20), use_container_width=True)
                st.json(infer_schema(df))

                cols = [""] + list(df.columns)
                mapping = st.session_state.mapping or {}
                origin_col = st.selectbox("Origin field", cols, index=cols.index(mapping.get("origin_col", "")))
                dev_col = st.selectbox("Development field (optional)", cols, index=cols.index(mapping.get("development_col") or ""))
                val_col = st.selectbox("Valuation field (optional)", cols, index=cols.index(mapping.get("valuation_col") or ""))
                value_col = st.selectbox("Value field", cols, index=cols.index(mapping.get("value_col", "")))
                grain = st.selectbox("Grain", ["annual", "semi-annual", "quarterly", "monthly"], index=0)
                input_type = st.radio("Input type", ["cumulative", "incremental"], horizontal=True)

                if st.button("Validate mappings"):
                    curr = {
                        "origin_col": origin_col or None,
                        "development_col": dev_col or None,
                        "valuation_col": val_col or None,
                        "value_col": value_col or None,
                        "grain": grain,
                        "input_type": input_type,
                    }
                    ok, msgs = validate_mapping(df, curr)
                    st.session_state.mapping = curr
                    st.session_state.validation_results = {"valid": ok, "messages": msgs}

                if st.session_state.validation_results:
                    st.write(st.session_state.validation_results)

    with tabs[1]:
        st.markdown("### Build actuarial development triangle")
        if st.session_state.raw_df is None:
            st.info("Load data first.")
        else:
            if st.button("Build Triangle"):
                valid = st.session_state.validation_results.get("valid", False)
                if not valid:
                    st.error("Validate mappings first.")
                else:
                    try:
                        result = build_triangle(st.session_state.raw_df, st.session_state.mapping)
                        st.session_state.triangle_result = result
                        st.session_state.triangle_definition = st.session_state.mapping
                        st.session_state.triangle_summary = {
                            "origins": int(result.cumulative_df.shape[0]),
                            "development_periods": int(result.cumulative_df.shape[1]),
                            "max_development_age": result.metadata["max_development_age"],
                        }
                        st.success("Triangle built successfully.")
                    except Exception as exc:
                        st.error(str(exc))

            tri_res = st.session_state.triangle_result
            if tri_res is not None:
                view = st.radio("View", ["Cumulative", "Incremental"], horizontal=True)
                df_show = tri_res.cumulative_df if view == "Cumulative" else tri_res.incremental_df
                _show_triangle(df_show, f"{view} Triangle")

    with tabs[2]:
        st.markdown("### Diagnostics")
        tri_res = st.session_state.triangle_result
        if tri_res is None:
            st.info("Build a triangle first.")
        else:
            ldf = deterministic_link_ratios(tri_res.cumulative_df)
            st.session_state.link_ratio_df = ldf
            _show_triangle(ldf, "Link Ratio Heatmap")
            findings = generate_findings(tri_res.cumulative_df, ldf)
            st.session_state.diagnostics = findings
            st.subheader("Structured findings")
            st.dataframe(pd.DataFrame(findings), use_container_width=True)

    with tabs[3]:
        st.markdown("### Pattern Detection")
        d = st.session_state.diagnostics
        if not d:
            st.info("Run diagnostics first.")
        else:
            df = pd.DataFrame(d)
            cats = df["category"].value_counts().reset_index()
            cats.columns = ["category", "count"]
            st.plotly_chart(px.bar(cats, x="category", y="count", title="Finding categories"), use_container_width=True)

            st.subheader("Override flagged ratios")
            if st.session_state.link_ratio_df is not None:
                link_cols = list(st.session_state.link_ratio_df.columns)
                ratio = st.selectbox("Ratio transition", link_cols)
                status = st.selectbox("Status", ["accepted", "excluded", "needs_review"])
                rationale = st.text_input("Rationale")
                if st.button("Save override"):
                    st.session_state.user_overrides[ratio] = {"status": status, "rationale": rationale}
            st.json(st.session_state.user_overrides)

    with tabs[4]:
        st.markdown("### Reserve Impact")
        tri_res = st.session_state.triangle_result
        if tri_res is None:
            st.info("Build a triangle first.")
        else:
            try:
                tri_cl = to_chainladder_triangle(tri_res.cumulative_df)
                outputs = run_chainladder_models(tri_cl)
                st.session_state.reserve_outputs = outputs
                st.subheader("LDF Table")
                st.dataframe(pd.DataFrame(outputs["ldf_table"]), use_container_width=True)
                st.subheader("Reserve Summary")
                rs = pd.DataFrame(outputs["reserve_summary"])
                st.dataframe(rs, use_container_width=True)
                if not rs.empty:
                    numeric_cols = rs.select_dtypes(include="number").columns
                    if len(numeric_cols) > 0:
                        chart_df = rs[[numeric_cols[0]]].reset_index(drop=True)
                        st.plotly_chart(px.line(chart_df, y=numeric_cols[0], title="Ultimate trend"), use_container_width=True)
                st.write("Bootstrap status:", outputs["bootstrap"])
            except Exception as exc:
                st.error(f"Chainladder calculation failed: {exc}")

    with tabs[5]:
        st.markdown("### AI Copilot")
        ctx = build_ai_context(st.session_state)
        st.session_state.ai_context = ctx
        st.caption("Evidence context (deterministic engine output)")
        st.json(ctx)

        actions = {
            "Explain key anomalies": ("summary", "Explain key anomalies in diagnostics."),
            "Challenge current factor selections": ("challenge", "Challenge current factor selections and exclusions."),
            "Summarise calendar year effects": ("summary", "Summarise potential calendar year effects."),
            "Draft reserve commentary": ("report", "Draft reserve commentary for workpapers."),
            "Highlight material risks": ("challenge", "Highlight material reserve risks."),
            "Generate management summary": ("report", "Generate concise management summary."),
        }
        cols = st.columns(3)
        for i, (label, (mode, prompt)) in enumerate(actions.items()):
            with cols[i % 3]:
                if st.button(label):
                    out = run_ai(mode, ctx, prompt)
                    st.session_state.ai_history.append(out)

        free_q = st.text_input("Freeform AI question")
        mode = st.selectbox("Mode", ["summary", "challenge", "report"])
        if st.button("Ask AI"):
            out = run_ai(mode, ctx, free_q)
            st.session_state.ai_history.append(out)

        for item in st.session_state.ai_history[-5:][::-1]:
            st.markdown(f"#### {item['mode'].title()} response")
            st.code(item["response"])
            st.caption(f"Evidence: {item['evidence']}")

    with tabs[6]:
        st.markdown("### Audit & Export")
        pack = build_audit_pack(st.session_state)

        st.download_button("Download diagnostics.json", to_json_bytes(st.session_state.get("diagnostics", [])), "diagnostics.json", "application/json")
        rs_df = pd.DataFrame(st.session_state.get("reserve_outputs", {}).get("reserve_summary", []))
        st.download_button("Download reserve_summary.csv", df_to_csv_bytes(rs_df if not rs_df.empty else pd.DataFrame()), "reserve_summary.csv", "text/csv")
        sel_df = pd.DataFrame([
            {"ratio": k, **v} for k, v in st.session_state.get("user_overrides", {}).items()
        ])
        st.download_button("Download selections.csv", df_to_csv_bytes(sel_df if not sel_df.empty else pd.DataFrame()), "selections.csv", "text/csv")
        st.download_button("Download ai_context.json", to_json_bytes(st.session_state.get("ai_context", {})), "ai_context.json", "application/json")

        report = "\n".join([f"### {x['mode'].title()}\n{x['response']}" for x in st.session_state.get("ai_history", [])]) or "No AI commentary yet."
        st.download_button("Download report_draft.md", report.encode("utf-8"), "report_draft.md", "text/markdown")

        st.download_button("Download full_audit_pack.json", to_json_bytes(pack), "full_audit_pack.json", "application/json")
        st.code(json.dumps(pack, indent=2, default=str)[:6000])
