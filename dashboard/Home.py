"""Python Script: Build a dashboard for data visualization (home page)"""
import streamlit as st


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text
    """
    st.title("SteamPulse")
    st.markdown("Insights for New Releases on Steam")
    st.markdown("---")


def sidebar_header() -> None:
    """
    Add text to the dashboard side bar
    """
    with st.sidebar:
        st.image("logo_one.png")


def dashboard_content() -> None:
    """
    Build content body for dashboard to help users navigate
    """
    st.markdown("### Overview")
    st.markdown(
        "You can navigate through the following sections:")
    st.markdown(
        "- Community: Explore data visualizations and insights that are relevant to steam community")
    st.markdown(
        "- Developer: Dive into technical data and analytics that developers will find valuable")
    st.markdown(
        "- New Releases: Explore all the latest game releases that power our visualizations")
    st.markdown(
        "- Subscription: Subscribe to SteamPulses emailing list to receive reports on new releases")

    st.markdown("#### Quick Tips:")
    st.markdown("- Use the filters to narrow down your search")
    st.markdown("- Hover over charts for full details")

    st.markdown("##### Sources:")
    st.markdown("- Steam Web Pages")
    st.markdown("- Steam Public API's")

    kausi_github = "https://github.com/gawsalya"
    hassan_github = "https://github.com/rhKashif"

    st.markdown("<br><br><br><br>",
                unsafe_allow_html=True)
    st.markdown("##### About us: Developers")
    st.markdown(
        "As well as being data engineers, each member of the team took on an additional role as follows:")
    st.markdown(
        "- [Daniel McCallion](https://github.com/DMcCallion) & [Angela Vilde](https://github.com/angelikavilde) - Project Managers")
    st.markdown("- [Kausi Mahasivam](%s) - Quality Assurance" % kausi_github)
    st.markdown("- [Hassan Kashif](%s) - Architect" % hassan_github)


if __name__ == "__main__":

    st.set_page_config(layout="wide")

    dashboard_header()
    sidebar_header()
    dashboard_content()
