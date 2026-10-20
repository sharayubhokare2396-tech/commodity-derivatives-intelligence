import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Commodity Derivatives Intelligence",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Commodity Derivatives Intelligence")
st.subheader("MCX Gold Relative Pricing Dashboard")
st.caption(
    "Hackpeak | Contract normalization, data validation "
    "and expiry-wise analysis"
)

st.info(
    "Data source: MCX Daily Bhavcopy. "
    "The saved dataset loads automatically; you can also upload "
    "another Bhavcopy file for analysis."
)

CONTRACTS = {
    "GOLDM": {"quoted_grams": 10, "purity": 995},
    "GOLDTEN": {"quoted_grams": 10, "purity": 999},
    "GOLDGUINEA": {"quoted_grams": 8, "purity": 999},
    "GOLDPETAL": {"quoted_grams": 1, "purity": 999},
}

REQUIRED_COLUMNS = ["Date", "Symbol", "Expiry Date", "Close"]

st.sidebar.header("Data")
uploaded_file = st.sidebar.file_uploader(
    "Optional: Upload another MCX Bhavcopy",
    type=["csv", "xlsx", "xls"]
)

try:
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".csv"):
            raw = pd.read_csv(uploaded_file, skiprows=4)
        else:
            raw = pd.read_excel(uploaded_file)

        st.sidebar.success("Using uploaded dataset")

    else:
        data_path = Path(__file__).parent / "gold_contracts_small.csv"

        if not data_path.exists():
            st.error(
                "Saved dataset not found. Check that "
                "gold_contracts_small.csv is committed beside app.py."
            )
            st.stop()

        # This processed CSV already has its header on the first row.
        raw = pd.read_csv(data_path)
        st.sidebar.success("Using saved MCX gold dataset")

except Exception as exc:
    st.error(f"Could not read dataset: {exc}")
    st.stop()

# Clean column names and padded symbol values
raw.columns = raw.columns.astype(str).str.strip()

st.subheader("1. File Validation")
st.metric("Uploaded rows", f"{len(raw):,}")

st.caption(
    "Dataset: September 2026 MCX gold futures bhavcopy. "
    "Contracts: GOLDM, GOLDTEN, GOLDGUINEA and GOLDPETAL."
)

missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]

if missing:
    st.error("Required columns missing: " + ", ".join(missing))
    st.write("Columns found:", raw.columns.tolist())
    st.stop()

df = raw.copy()
df["Symbol"] = df["Symbol"].astype(str).str.strip().str.upper()
df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)

# MCX expiry format commonly looks like 04SEP2026
df["Expiry Date"] = pd.to_datetime(
    df["Expiry Date"].astype(str).str.strip(),
    format="%d%b%Y",
    errors="coerce"
)

if "Instrument Name" in df.columns:
    df = df[df["Instrument Name"].astype(str).str.strip().str.upper() == "FUTCOM"]

gold = df[df["Symbol"].isin(CONTRACTS)].copy()

if gold.empty:
    st.warning(
        "No supported gold futures contracts found. "
        "Check the symbol names and instrument type in your file."
    )
    st.write("Symbols found:", sorted(df["Symbol"].dropna().unique())[:50])
    st.stop()

gold["Close"] = pd.to_numeric(gold["Close"], errors="coerce")
gold = gold.dropna(subset=["Date", "Expiry Date", "Close"])
gold = gold[gold["Close"] > 0].copy()

if "Volume(Lots)" in gold.columns:
    gold["Volume(Lots)"] = pd.to_numeric(
        gold["Volume(Lots)"], errors="coerce"
    )

if "Open Interest(Lots)" in gold.columns:
    gold["Open Interest(Lots)"] = pd.to_numeric(
        gold["Open Interest(Lots)"], errors="coerce"
    )
if "Instrument Name" in raw.columns:
    st.write("Instrument types:", raw["Instrument Name"].value_counts())

duplicate_keys = ["Date", "Symbol", "Expiry Date"]

duplicate_count = gold.duplicated(
    subset=duplicate_keys
).sum()

if duplicate_count > 0:
    st.warning(
        f"Found {duplicate_count} duplicate date-contract-expiry rows. "
        "Review duplicates before using this data for backtesting."
    )

    dup_rows = gold[
        gold.duplicated(subset=duplicate_keys, keep=False)
    ].sort_values(duplicate_keys)

    st.subheader("Duplicate Row Investigation")
    st.dataframe(dup_rows, use_container_width=True)
   
# Calculate equivalent price per gram at 999 purity.
# Close is quoted per the contract's quoted_grams basis.
gold["Quoted grams"] = gold["Symbol"].map(
    {k: v["quoted_grams"] for k, v in CONTRACTS.items()}
)
gold["Purity"] = gold["Symbol"].map(
    {k: v["purity"] for k, v in CONTRACTS.items()}
)

gold["Normalized ₹/g (999)"] = (
    gold["Close"] / gold["Quoted grams"]
    * 999 / gold["Purity"]
)

gold = gold.sort_values(["Date", "Expiry Date", "Symbol"])
# Historical analysis: aggregate repeated rows without deleting data
daily_prices = (
    gold.groupby(["Date", "Symbol", "Expiry Date"], as_index=False)
    ["Normalized ₹/g (999)"]
    .median()
    .sort_values(["Symbol", "Expiry Date", "Date"])
)

# Rolling Z-score using only previous 5 observations
grouped_prices = daily_prices.groupby(["Symbol", "Expiry Date"])[
    "Normalized ₹/g (999)"
]

# Shift(1) excludes the current day's price
previous_prices = grouped_prices.shift(1)

daily_prices["Rolling Mean"] = (
    previous_prices.groupby(
        [daily_prices["Symbol"], daily_prices["Expiry Date"]]
    )
    .transform(lambda s: s.rolling(window=5, min_periods=5).mean())
)

daily_prices["Rolling Std"] = (
    previous_prices.groupby(
        [daily_prices["Symbol"], daily_prices["Expiry Date"]]
    )
    .transform(lambda s: s.rolling(window=5, min_periods=5).std(ddof=0))
)

daily_prices["Z-score"] = (
    (daily_prices["Normalized ₹/g (999)"] - daily_prices["Rolling Mean"])
    / daily_prices["Rolling Std"].replace(0, float("nan"))
)

st.subheader("Historical Price Trends")

trend_fig = px.line(
    daily_prices,
    x="Date",
    y="Normalized ₹/g (999)",
    color="Symbol",
    facet_col="Symbol",
    facet_col_wrap=2,
    hover_data=["Expiry Date"],
    title="Normalized Gold Prices Over Time"
)
st.plotly_chart(trend_fig, use_container_width=True)

st.subheader("Rolling Z-score Analysis")
st.caption(
    "Uses the previous five observations within each contract expiry. "
    "Z-scores are exploratory indicators, not validated trading signals."
)

zscore_fig = px.line(
    daily_prices,
    x="Date",
    y="Z-score",
    color="Symbol",
    facet_col="Symbol",
    facet_col_wrap=2,
    hover_data=["Expiry Date"],
    title="Five-Observation Rolling Z-score"
)
st.plotly_chart(zscore_fig, use_container_width=True)

st.dataframe(
    daily_prices,
    use_container_width=True,
    hide_index=True
)

c1, c2, c3 = st.columns(3)
c1.metric("Gold records", f"{len(gold):,}")
c2.metric("Contracts found", gold["Symbol"].nunique())
c3.metric("Trading dates", gold["Date"].nunique())

st.success("File loaded and supported gold rows processed.")

st.subheader("2. Normalized Gold Contract Prices")
st.caption(
    "Prices are expressed as equivalent ₹/gram at 999 purity. "
    "Expiry dates remain separate; this is not a trading signal."
)

display_cols = [
    "Date", "Symbol", "Expiry Date", "Close",
    "Quoted grams", "Purity", "Normalized ₹/g (999)"
]

for optional_col in ["Volume(Lots)", "Open Interest(Lots)"]:
    if optional_col in gold.columns:
        display_cols.append(optional_col)

st.dataframe(
    gold[display_cols],
    use_container_width=True,
    hide_index=True
)

st.subheader("3. Price Comparison")
plot_data = gold.copy()
plot_data["Expiry Label"] = plot_data["Expiry Date"].dt.strftime("%d %b %Y")

fig = px.scatter(
    plot_data,
    x="Expiry Date",
    y="Normalized ₹/g (999)",
    color="Symbol",
    hover_data=["Date", "Close", "Purity"],
    title="Normalized Gold Prices by Contract Expiry"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("4. Data Quality Summary")
q1, q2, q3 = st.columns(3)
q1.metric("Missing dates in uploaded file", int(raw["Date"].isna().sum()))
q2.metric("Invalid/zero gold prices removed",
          int((pd.to_numeric(
              df.loc[df["Symbol"].isin(CONTRACTS), "Close"],
              errors="coerce"
          ) <= 0).sum()))
q3.metric("Duplicate gold rows", int(duplicate_count))

st.subheader("5. Download Processed Gold Data")
csv_data = gold[display_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    "Download normalized gold CSV",
    data=csv_data,
    file_name="normalized_gold_contracts.csv",
    mime="text/csv"
)

st.subheader("Current Limitations")
st.markdown("""
- Normalized prices are an analytical comparison, not proof of mispricing.
- Contracts with different expiry dates may have different carry and expiry effects.
- A single trading day cannot validate a historical strategy.
- Backtesting, transaction-cost modelling and unseen-data evaluation
  are not implemented in this version.
- Settlement prices are not guaranteed executable trade prices.
- Volume is not market depth or guaranteed liquidity.
""")

st.caption("Commodity Derivatives Intelligence | Hackpeak")
