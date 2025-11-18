import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Revenue vs Expenditure Dashboard", layout="wide")

st.title("Revenue vs Expenditure — 10+ Years")
st.markdown("Interactive dashboard to visualize company revenue vs expenditure trends.")

# --- Data loading ---
default_csv = Path("data/revenue_data.csv")
uploaded = st.sidebar.file_uploader("Upload CSV (columns: year,revenue,expenditure)", type=["csv", "xlsx"])

if uploaded is not None:
    if str(uploaded).lower().endswith(".xlsx") or hasattr(uploaded, "read"):
        try:
            df = pd.read_excel(uploaded) if str(uploaded).lower().endswith(".xlsx") else pd.read_csv(uploaded)
        except Exception:
            uploaded.seek(0)
            df = pd.read_csv(uploaded)
else:
    df = pd.read_csv(default_csv)

# Basic validation and cleaning
expected_cols = {"year", "revenue", "expenditure"}
if not expected_cols.issubset({c.lower() for c in df.columns}):
    st.error(f"Data must contain columns: {expected_cols}. Found: {list(df.columns)}")
    st.stop()

# Normalize column names
df = df.rename(columns={c: c.lower() for c in df.columns})
df = df[["year", "revenue", "expenditure"]].copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0)
df["expenditure"] = pd.to_numeric(df["expenditure"], errors="coerce").fillna(0)
df = df.sort_values("year").reset_index(drop=True)

# Sidebar controls
st.sidebar.markdown("### Controls")
min_year, max_year = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", min_year, max_year, (min_year, max_year))

df_filtered = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

# KPIs
col1, col2, col3, col4 = st.columns(4)
latest = df_filtered.iloc[-1] if not df_filtered.empty else None
total_revenue = df_filtered["revenue"].sum()
total_expenditure = df_filtered["expenditure"].sum()
avg_revenue = df_filtered["revenue"].mean() if not df_filtered.empty else 0
avg_expenditure = df_filtered["expenditure"].mean() if not df_filtered.empty else 0

col1.metric("Total Revenue", f"${int(total_revenue):,}")
col2.metric("Total Expenditure", f"${int(total_expenditure):,}")
col3.metric("Average Revenue (yr)", f"${int(avg_revenue):,}")
col4.metric("Average Expenditure (yr)", f"${int(avg_expenditure):,}")

# Chart
st.subheader("Revenue vs Expenditure (Line Chart)")
if df_filtered.empty:
    st.info("No data in the selected year range.")
else:
    fig = px.line(
        df_filtered,
        x="year",
        y=["revenue", "expenditure"],
        labels={"value": "USD", "year": "Year", "variable": "Series"},
        markers=True,
        template="plotly_dark",
        title=f"Revenue and Expenditure ({year_range[0]} — {year_range[1]})",
    )
    fig.update_layout(legend=dict(y=0.99, x=0.01))
    fig.update_yaxes(tickprefix="$", separatethousands=True)
    st.plotly_chart(fig, use_container_width=True)

# Data table and download
st.subheader("Data (filtered)")
st.dataframe(df_filtered.style.format({"revenue": "${:,.0f}", "expenditure": "${:,.0f}"}))

csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", data=csv_bytes, file_name="revenue_filtered.csv", mime="text/csv")

st.markdown("---")
st.caption("Replace the sample CSV in `data/revenue_data.csv` with your actual data (columns: year, revenue, expenditure).")
