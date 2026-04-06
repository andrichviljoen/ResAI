import streamlit as st


def initialize_state() -> None:
    defaults = {
        "raw_df": None,
        "dataset_info": {},
        "mapping": {},
        "validation_results": {},
        "triangle_result": None,
        "triangle_definition": {},
        "triangle_summary": {},
        "link_ratio_df": None,
        "diagnostics": [],
        "selected_factors": {},
        "user_overrides": {},
        "reserve_outputs": {},
        "ai_context": {},
        "ai_history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
