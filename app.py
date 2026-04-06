import streamlit as st

from actuarygpt_workbench.components.state import initialize_state
from actuarygpt_workbench.pages.main_workspace import render_workspace

st.set_page_config(page_title="ActuaryGPT Triangle Diagnostic Workbench", layout="wide")
initialize_state()
render_workspace()
