import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Commodity Derivatives Intelligence",
    page_icon="📈",
    layout="wide"
)

# Header
st.title("📈 Commodity Derivatives Intelligence")
st.markdown(
    "### MCX Gold Market Analysis Dashboard"
)
st.caption(
    "Gold contract normalization | Relative pricing | Backtesting"
)

st.divider()

# Project overview
st.subheader("Project Overview")
st.write(
    "This project aims to compare MCX gold futures contracts "
    "on a common basis to identify potential relative mispricing."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.info("**GOLDM**\n\nGold Mini contract")

with col2:
    st.info("**GOLDTEN**\n\nGold Ten contract")

with col3:
    st.info("**GOLDGUINEA / GOLDPETAL**\n\nOther gold contracts")

st.divider()

# Validation metrics
st.subheader("Validation Status")

col1, col2, col3 = st.columns(3)

col1.metric("Net PnL after costs", "Not validated")
col2.metric("Unseen-data hit rate", "Not measured")
col3.metric("Gold price contribution", "Not evaluated")

st.warning(
    "Historical MCX data and backtest results have not yet "
    "been validated. No performance figures are claimed."
)

st.divider()

# Upload market data
st.subheader("Upload MCX Bhavcopy")
st.write(
    "Upload a historical MCX CSV or Excel file to inspect "
    "its columns and data before analysis."
)

uploaded_file = st.file_uploader(
    "Choose a market data file",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File loaded for preview.")
        st.write("Rows:", len(df))
        st.write("Columns:", len(df.columns))
        st.dataframe(df.head(20), use_container_width=True)

        st.download_button(
            "Download uploaded data preview",
            data=df.head(1000).to_csv(index=False).encode("utf-8"),
            file_name="mcx_data_preview.csv",
            mime="text/csv"
        )

    except Exception as error:
        st.error(f"Could not read the file: {error}")

st.divider()

# Methodology
st.subheader("Proposed Analysis Workflow")

st.markdown("""
1. **Data Collection:** Obtain historical MCX Bhavcopy data.
2. **Data Validation:** Check dates, contracts, prices and units.
3. **Normalization:** Convert contracts to a comparable basis
   using verified contract specifications.
4. **Relative Pricing:** Compare normalized contract prices.
5. **Walk-forward Backtesting:** Test signals on unseen periods
   while accounting for costs and liquidity.
6. **Performance Evaluation:** Report PnL and other metrics only
   after testing and verification.
""")

st.divider()

st.subheader("Limitations")

st.markdown("""
- Performance results have not yet been verified.
- Settlement prices may differ from executable trade prices.
- Contract specifications and quotation units must be verified.
- This prototype is for educational and hackathon demonstration
  purposes, not financial advice.
""")

st.caption("Commodity Derivatives Intelligence | Hackpeak Project")