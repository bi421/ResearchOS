# dashboard_app.py
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# PAGE CONFIG
st.set_page_config(page_title="ðŸ“Š ResearchOS Dashboard", layout="wide")

st.title("ðŸš€ ResearchOS - Multi-Strategy Backtest Dashboard")
st.markdown("Ð‘Ò¯Ñ… ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸Ð¹Ð½ Ò¯Ñ€ Ð´Ò¯Ð½Ð³ Ð½ÑÐ³ Ð´Ð¾Ñ€Ð¾Ð¾Ñ Ñ…Ð°Ñ€Ð¶, ÑˆÒ¯Ò¯Ð¶, Ð´Ò¯Ð½ ÑˆÐ¸Ð½Ð¶Ð¸Ð»Ð³ÑÑ Ñ…Ð¸Ð¹Ñ…")


# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("backtest_results_all.csv")
    df = df[df["Trades"] > 0]  # 0 Ð°Ñ€Ð¸Ð»Ð³Ð°Ð°Ñ‚Ð°Ð¹ Ð¼Ó©Ñ€Ò¯Ò¯Ð´Ð¸Ð¹Ð³ Ñ…Ð°ÑÐ°Ñ…
    return df


df = load_data()

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.header("ðŸ” Ð¨Ò¯Ò¯Ð»Ñ‚Ò¯Ò¯Ñ€")

strategies = st.sidebar.multiselect("Ð¡Ñ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸ ÑÐ¾Ð½Ð³Ð¾Ñ…", options=sorted(df["Strategy"].unique()), default=sorted(df["Strategy"].unique()))

timeframes = st.sidebar.multiselect("Timeframe ÑÐ¾Ð½Ð³Ð¾Ñ…", options=sorted(df["Timeframe"].unique()), default=sorted(df["Timeframe"].unique()))

min_trades = st.sidebar.slider("Ð¥Ð°Ð¼Ð³Ð¸Ð¹Ð½ Ð±Ð°Ð³Ð° Ð°Ñ€Ð¸Ð»Ð³Ð°Ð°Ð½Ñ‹ Ñ‚Ð¾Ð¾", min_value=int(df["Trades"].min()), max_value=int(df["Trades"].max()), value=10)

# Filter data
filtered_df = df[(df["Strategy"].isin(strategies)) & (df["Timeframe"].isin(timeframes)) & (df["Trades"] >= min_trades)]

# ============================================================
# MAIN METRICS
# ============================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("ðŸ“Š ÐÐ¸Ð¹Ñ‚ Ñ‚ÐµÑÑ‚", len(filtered_df))
with col2:
    best_return = filtered_df.loc[filtered_df["Return"].idxmax()] if not filtered_df.empty else None
    if best_return is not None:
        st.metric("ðŸ† Ð¥Ð°Ð¼Ð³Ð¸Ð¹Ð½ Ó©Ð½Ð´Ó©Ñ€ Ó©Ð³Ó©Ó©Ð¶", f"{best_return['Return']:.2f}%", f"{best_return['Strategy']} @ {best_return['Timeframe']}")
with col3:
    best_sharpe = filtered_df.loc[filtered_df["Sharpe"].idxmax()] if not filtered_df.empty else None
    if best_sharpe is not None:
        st.metric("ðŸ“ˆ Ð¥Ð°Ð¼Ð³Ð¸Ð¹Ð½ Ó©Ð½Ð´Ó©Ñ€ Sharpe", f"{best_sharpe['Sharpe']:.2f}", f"{best_sharpe['Strategy']} @ {best_sharpe['Timeframe']}")
with col4:
    most_trades = filtered_df.loc[filtered_df["Trades"].idxmax()] if not filtered_df.empty else None
    if most_trades is not None:
        st.metric("ðŸ”„ Ð¥Ð°Ð¼Ð³Ð¸Ð¹Ð½ Ð¾Ð»Ð¾Ð½ Ð°Ñ€Ð¸Ð»Ð³Ð°Ð°", f"{most_trades['Trades']:,}", f"{most_trades['Strategy']} @ {most_trades['Timeframe']}")

# ============================================================
# DATA TABLE
# ============================================================
st.subheader("ðŸ“‹ Ò®Ñ€ Ð´Ò¯Ð½Ð³Ð¸Ð¹Ð½ Ñ…Ò¯ÑÐ½ÑÐ³Ñ‚")
st.dataframe(filtered_df.style.background_gradient(subset=["Return", "Sharpe"], cmap="RdYlGn"), use_container_width=True, height=400)

# ============================================================
# CHARTS
# ============================================================
st.subheader("ðŸ“ˆ Ð“Ñ€Ð°Ñ„Ð¸Ðº ÑˆÐ¸Ð½Ð¶Ð¸Ð»Ð³ÑÑ")

col1, col2 = st.columns(2)

with col1:
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    pivot_return = filtered_df.pivot_table(index="Strategy", columns="Timeframe", values="Return", aggfunc="mean")
    pivot_return.plot(kind="bar", ax=ax1, colormap="viridis")
    ax1.set_title("Return by Strategy and Timeframe")
    ax1.set_ylabel("Return (%)")
    ax1.legend(title="Timeframe", bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45)
    st.pyplot(fig1)

with col2:
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    pivot_sharpe = filtered_df.pivot_table(index="Strategy", columns="Timeframe", values="Sharpe", aggfunc="mean")
    pivot_sharpe.plot(kind="bar", ax=ax2, colormap="plasma")
    ax2.set_title("Sharpe Ratio by Strategy and Timeframe")
    ax2.set_ylabel("Sharpe Ratio")
    ax2.legend(title="Timeframe", bbox_to_anchor=(1.05, 1))
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# Scatter plot: Return vs Sharpe
st.subheader("ðŸ“Œ Return vs Sharpe (ÐÑ€Ð¸Ð»Ð³Ð°Ð°Ð½Ñ‹ Ñ‚Ð¾Ð¾Ð³Ð¾Ð¾Ñ€ Ó©Ð½Ð³Ó©Ð»ÑÓ©Ð½)")
fig3, ax3 = plt.subplots(figsize=(12, 7))
scatter = ax3.scatter(filtered_df["Sharpe"], filtered_df["Return"], c=filtered_df["Trades"], cmap="viridis", s=100, alpha=0.8)
plt.colorbar(scatter, label="Number of Trades")
ax3.set_xlabel("Sharpe Ratio")
ax3.set_ylabel("Return (%)")
ax3.set_title("Return vs Sharpe Ratio")
# Annotate top points
for idx, row in filtered_df.nlargest(10, "Return").iterrows():
    ax3.annotate(f"{row['Strategy'][:4]} {row['Timeframe']}", (row["Sharpe"], row["Return"]), fontsize=8, alpha=0.7)
st.pyplot(fig3)

# ============================================================
# TOP PERFORMERS
# ============================================================
st.subheader("ðŸ† Ð¨Ð¸Ð»Ð´ÑÐ³ ÑÑ‚Ñ€Ð°Ñ‚ÐµÐ³Ð¸ÑƒÐ´ (ÐÑ€Ð¸Ð»Ð³Ð°Ð°Ð½Ñ‹ Ñ‚Ð¾Ð¾ 50-Ñ Ð´ÑÑÑˆ)")
top_df = filtered_df[filtered_df["Trades"] >= 50]

col1, col2 = st.columns(2)

with col1:
    st.markdown("**ðŸ“ˆ Ó¨Ð³Ó©Ó©Ð¶Ó©Ó©Ñ€ ÑÑ€ÑÐ¼Ð±ÑÐ»ÑÑÐ½ (Return)**")
    top_return = top_df.nlargest(5, "Return")
    st.dataframe(top_return[["Strategy", "Timeframe", "Trades", "Return", "Sharpe"]].reset_index(drop=True))

with col2:
    st.markdown("**ðŸ“Š Sharpe-ÑÑÑ€ ÑÑ€ÑÐ¼Ð±ÑÐ»ÑÑÐ½**")
    top_sharpe = top_df.nlargest(5, "Sharpe")
    st.dataframe(top_sharpe[["Strategy", "Timeframe", "Trades", "Return", "Sharpe"]].reset_index(drop=True))

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.caption(f"âœ… Ó¨Ð³Ó©Ð³Ð´Ó©Ð» ÑˆÐ¸Ð½ÑÑ‡Ð»ÑÐ³Ð´ÑÑÐ½: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} | ÐÐ¸Ð¹Ñ‚ {len(filtered_df)} Ñ‚ÐµÑÑ‚")
