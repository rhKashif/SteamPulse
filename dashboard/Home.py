"""Python Script: Build a dashboard for data visualization"""
from datetime import datetime
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
import streamlit as st
from psycopg2 import connect
from psycopg2.extensions import connection


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text

    Args:
        None

    Returns:
        None
    """
    st.title("SteamPulse")
    st.markdown("Community Insights for New Releases on Steam")
    st.markdown("---")


def sidebar_header() -> None:
    """
    Add text to the dashboard side bar

    Args:
        None

    Returns:
        None
    """
    with st.sidebar:
        st.image("logo_one.png")


def dashboard_content() -> None:
    """
    Build content body for dashboard to help users navigate

    Args:
        None

    Returns:
        None
    """
    st.markdown("### Dashboard Overview")
    st.markdown(
        "This dashboard is designed to cater to different audiences.You can navigate through the following sections:")
    st.markdown(
        "- Community: Explore data visualizations and insights that are relevant to steam community")
    st.markdown(
        "- Developer: Dive into technical data and analytics that developers will find valuable")
    st.markdown(
        "- New Releases: Explore all the latest game releases that power our visualizations")

    st.markdown("#### Quick Tips:")
    st.markdown("- Use the filters to narrow down your search")
    st.markdown("- Hover over charts for additional details")

    st.markdown("##### Sources:")
    st.markdown("- Steam Web Pages")
    st.markdown("- Steam Public API's")

    st.markdown("<br><br><br><br>",
                unsafe_allow_html=True)
    st.markdown("##### About us: Developers")
    st.markdown(
        "This Dashboard has been build as part of the Sigma Labs final project:")
    st.markdown("- Daniel McCallion & Angela Vilde - Project Managers")
    st.markdown("- Kausi Mahasivam - Quality Assurance")
    st.markdown("- Hassan Kashif - Architect")


if __name__ == "__main__":

    st.set_page_config(layout="wide")

    dashboard_header()
    sidebar_header()
    dashboard_content()
