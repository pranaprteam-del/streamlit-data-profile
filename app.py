import streamlit as st
import pandas as pd
from ydata_profiling import ProfileReport
from streamlit_ydata_profiling import st_profile_report  # Updated import for modern ydata-profiling
import os

# ======================================================
# Page configuration
# ======================================================
st.set_page_config(
    page_title="Data Profiler",
    layout="wide"
)

# ======================================================
# Helper functions
# ======================================================
def get_filesize_mb(file) -> float:
    """Return uploaded file size in MB"""
    return file.size / (1024 ** 2)

def validate_file(file):
    """Allow only CSV and Excel files"""
    _, ext = os.path.splitext(file.name.lower())
    if ext in (".csv", ".xlsx"):
        return ext
    return None

# ======================================================
# Sidebar
# ======================================================
with st.sidebar:
    st.header("📁 Upload Data")
    uploaded_file = st.file_uploader(
        "Upload .csv or .xlsx (Max 10 MB)",
        type=["csv", "xlsx"]
    )
    # Profiling options
    minimal = True
    enable_wc = True  # Default: WordClouds enabled
    if uploaded_file:
        st.subheader("⚙️ Profiling Options")
        minimal = st.checkbox(
            "Generate minimal report (faster)",
            value=True
        )
        enable_wc = st.checkbox(
            "Enable WordClouds (for text columns)",
            value=True
        )

# ======================================================
# Main App Logic
# ======================================================
if uploaded_file:
    # ---------- Validate file ----------
    ext = validate_file(uploaded_file)
    if not ext:
        st.error("❌ Only .csv and .xlsx files are supported.")
        st.stop()

    # ---------- Validate file size ----------
    filesize = get_filesize_mb(uploaded_file)
    if filesize > 10:
        st.error(
            f"❌ Maximum allowed size is 10 MB. "
            f"Uploaded file is {filesize:.2f} MB."
        )
        st.stop()

    # ---------- Load data ----------
    try:
        if ext == ".csv":
            df = pd.read_csv(uploaded_file)
        else:
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_name = st.sidebar.selectbox(
                "Select Excel sheet",
                excel_file.sheet_names
            )
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
        st.stop()

    # ---------- Preview ----------
    st.subheader("🔍 Data Preview")
    st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
    st.dataframe(df.head())

    # ---------- Profiling ----------
    st.subheader("📊 Data Profiling Report")
    with st.spinner("Generating profiling report..."):
        profile = ProfileReport(
            df,
            minimal=minimal,
            explorative=True,
            pool_size=1,  # Safer for Streamlit
            correlations=None,  # Avoids heavy calculations
            html={"style": {"full_width": True}},
            plot={"wordcloud": enable_wc}  # Enable/disable WordClouds based on user choice
        )
    # Render report in Streamlit
    st_profile_report(profile)

else:
    st.title("📊 Data Profiler App")
    st.info(
        "Upload a CSV or Excel file from the sidebar to generate "
        "an automated data profiling report."
    )