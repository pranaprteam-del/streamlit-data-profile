import streamlit as st
import pandas as pd
from io import BytesIO
import chardet

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Multi-File Preview, Append & Download",
    layout="wide"
)

st.title("📂 Multi CSV / Excel Preview, Append & Download")

# ---------------- File Uploader ----------------
uploaded_files = st.file_uploader(
    "Upload CSV or Excel files",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

# ---------------- Helper Functions ----------------
def read_csv_safely(file):
    raw = file.read()
    encoding = chardet.detect(raw)["encoding"]

    return pd.read_csv(
        BytesIO(raw),
        encoding=encoding,
        sep=None,
        engine="python",
        on_bad_lines="skip"
    )

def read_excel_safely(file):
    filename = file.name.lower()

    if filename.endswith(".xls"):
        try:
            return pd.read_excel(file, engine="xlrd")
        except Exception:
            file.seek(0)
            tables = pd.read_html(file)
            return tables[0]
    else:
        return pd.read_excel(file, engine="openpyxl")

def fix_headers_if_needed(df):
    # If column headers are numeric, promote first valid row as header
    if all(isinstance(col, int) for col in df.columns):
        header_row_idx = None
        for i in range(len(df)):
            if df.iloc[i].notna().sum() > 0:
                header_row_idx = i
                break

        if header_row_idx is not None:
            df.columns = df.iloc[header_row_idx]
            df = df.iloc[header_row_idx + 1:].reset_index(drop=True)

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
    )

    return df

def export_to_excel(raw_dfs, combined_df, summary_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        combined_df.to_excel(writer, index=False, sheet_name="Combined_Data")
        summary_df.to_excel(writer, index=False, sheet_name="File_Summary")

        for name, df in raw_dfs.items():
            sheet_name = name[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)

    return output.getvalue()

# ---------------- Main Logic ----------------
if uploaded_files:
    raw_dfs = {}
    combined_list = []

    st.header("🔍 File Previews (50 rows per file)")

    for file in uploaded_files:
        try:
            # -------- Read full file --------
            if file.name.lower().endswith(".csv"):
                df = read_csv_safely(file)
            else:
                df = read_excel_safely(file)

            # -------- Fix headers if needed --------
            df = fix_headers_if_needed(df)

            # -------- Add metadata --------
            df["source_file"] = file.name

            # -------- Store FULL data --------
            raw_dfs[file.name] = df
            combined_list.append(df)

            # -------- Preview ONLY --------
            with st.expander(f"📄 {file.name}"):
                st.dataframe(df.head(50), use_container_width=True)
                st.caption(f"Rows: {df.shape[0]} | Columns: {df.shape[1]}")

        except Exception as e:
            st.error(f"❌ Failed to read {file.name}: {e}")

    if combined_list:
        # -------- Append FULL data --------
        combined_df = pd.concat(combined_list, ignore_index=True)

        # -------- Summary --------
        summary_df = (
            combined_df.groupby("source_file")
            .size()
            .reset_index(name="Row_Count")
        )

        st.header("📊 Combined Preview (first 100 rows only)")
        st.dataframe(combined_df.head(100), use_container_width=True)
        st.caption(
            f"Total Rows: {combined_df.shape[0]} | "
            f"Total Columns: {combined_df.shape[1]}"
        )

        # -------- Download FULL data --------
        excel_data = export_to_excel(raw_dfs, combined_df, summary_df)

        st.subheader("💾 Save As")

        custom_filename = st.text_input(
            "Enter file name",
            value="combined_output.xlsx"
        )

        if not custom_filename.lower().endswith(".xlsx"):
            custom_filename += ".xlsx"

        st.download_button(
            label="⬇️ Download Combined Excel (FULL DATA)",
            data=excel_data,
            file_name=custom_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Upload one or more CSV / Excel files to begin.")
