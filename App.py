import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import ta
import yfinance as yf

# 1. Page Layout Config (Optimized for Laptop & iPhone 12)
st.set_page_config(
    page_title='Pro AI Stock Terminal', page_icon='⚡', layout='wide'
)

# Custom CSS for Mobile & Pro Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.title('⚡ Pro AI Stock Analysis Terminal')
st.caption(
    'Enterprise-Grade Fundamental & Technical Screener | Designed for Web &'
    ' Mobile'
)

# Sidebar Tickers Input & Market Preset
st.sidebar.header('⚙️ Screener Controls')
market_preset = st.sidebar.selectbox(
    'Select Market Watchlist', [
        'Custom Tickers',
        'Top Indian Giants (Nifty 50)',
        'Top US Tech Stocks',
    ]
)

if market_preset == 'Top Indian Giants (Nifty 50)':
  default_tickers = 'RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS, ITC.NS, SBIN.NS, BHARTIARTL.NS, LTIM.NS, HINDUNILVR.NS'
elif market_preset == 'Top US Tech Stocks':
  default_tickers = 'AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META'
else:
  default_tickers = (
      'RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, AAPL, MSFT, GOOGL'
  )

user_input = st.sidebar.text_area(
    'Enter Tickers (comma separated):', default_tickers
)
tickers = [t.strip() for t in user_input.split(',') if t.strip()]

timeframe = st.sidebar.selectbox(
    'Technical Timeframe', ['6mo', '1y', '2y', '5y'], index=1
)


# Advanced Financial & Technical Engine
@st.cache_data(ttl=3600)
def fetch_pro_stock_data(ticker_list, period_val):
  terminal_results = []
  for t in ticker_list:
    try:
      stock = yf.Ticker(t)
      info = stock.info

      hist = stock.history(period=period_val)
      if hist.empty:
        continue

      current_price = hist['Close'].iloc[-1]
      prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
      price_change_pct = ((current_price - prev_close) / prev_close) * 100

      # Technical Indicators (RSI, MACD, Moving Averages)
      hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
      hist['SMA_200'] = hist['Close'].rolling(window=200).mean()

      rsi_ind = ta.momentum.RSIIndicator(close=hist['Close'])
      hist['RSI'] = rsi_ind.rsi()
      current_rsi = hist['RSI'].iloc[-1] if not hist['RSI'].empty else 50

      macd_ind = ta.trend.MACD(close=hist['Close'])
      hist['MACD'] = macd_ind.macd()
      hist['MACD_Signal'] = macd_ind.macd_signal()

      # Fundamentals Extraction
      pe = info.get('trailingPE', 0) or 0
      pb = info.get('priceToBook', 0) or 0
      roe = (info.get('returnOnEquity', 0) or 0) * 100
      debt_eq = (info.get('debtToEquity', 100) or 100) / 100
      market_cap = info.get('marketCap', 0) or 0
      div_yield = (info.get('dividendYield', 0) or 0) * 100
      sector = info.get('sector', 'General')

      # Professional Scoring Logic (Max 100)
      score = 0
      health_tags = []

      if 0 < pe < 35:
        score += 20
        health_tags.append('Fair Valuation')
      if roe > 15:
        score += 25
        health_tags.append('High ROE')
      if debt_eq < 1.0:
        score += 20
        health_tags.append('Low Debt Risk')
      if current_price > hist['SMA_50'].iloc[-1]:
        score += 20
        health_tags.append('Bullish Trend (50 SMA)')
      if 40 <= current_rsi <= 65:
        score += 15
        health_tags.append('Optimal RSI')

      terminal_results.append({
          'Ticker': t,
          'Sector': sector,
          'Price': round(current_price, 2),
          'Change (%)': round(price_change_pct, 2),
          'Market Cap': (
              f'₹{market_cap / 1e7:.2f} Cr'
              if '.NS' in t
              else f'${market_cap / 1e9:.2f} B'
          ),
          'P/E': round(pe, 2),
          'P/B': round(pb, 2),
          'ROE (%)': round(roe, 2),
          'Debt/Eq': round(debt_eq, 2),
          'Div Yield (%)': round(div_yield, 2),
          'RSI': round(current_rsi, 2),
          'Score': score,
          'Health Tags': ', '.join(health_tags),
          'History': hist,
      })
    except Exception:
      continue
  return terminal_results


# Main Execution Trigger
if st.button('🚀 Run Pro Market Scan') or 'terminal_data' in st.session_state:
  if (
      'terminal_data' not in st.session_state
      or st.sidebar.button('Force Refresh')
  ):
    with st.spinner(
        'Analyzing fundamentals & crunching technical indicators...'
    ):
      st.session_state.terminal_data = fetch_pro_stock_data(tickers, timeframe)

  data = st.session_state.terminal_data
  if data:
    df = pd.DataFrame(data)
    df_sorted = df.sort_values(by='Score', ascending=False)

    # Top Metric Overview Cards
    st.subheader('🏆 Market Leaders & Health Scorecard')
    st.dataframe(
        df_sorted[[
            'Ticker',
            'Sector',
            'Price',
            'Change (%)',
            'Score',
            'P/E',
            'ROE (%)',
            'RSI',
            'Health Tags',
        ]],
        use_container_width=True,
    )

    st.divider()

    # Deep-Dive Section with Tabs
    st.subheader('🔍 Deep-Dive Asset Inspection')
    selected_stock_symbol = st.selectbox(
        'Choose Stock to Inspect:', df_sorted['Ticker'].tolist()
    )

    stock_detail = next(
        item for item in data if item['Ticker'] == selected_stock_symbol
    )
    hist_df = stock_detail['History']

    # Tabs for Professional Organization
    tab_chart, tab_fundamentals, tab_ai = st.tabs([
        '📈 Pro Candlestick & Indicators',
        '📊 Fundamental Metrics',
        '🤖 AI Verdict & Insights',
    ])

    with tab_chart:
      # Advanced Plotly Candlestick with Subplots Layout concept
      fig = go.Figure()
      fig.add_trace(
          go.Candlestick(
              x=hist_df.index,
              open=hist_df['Open'],
              high=hist_df['High'],
              low=hist_df['Low'],
              close=hist_df['Close'],
              name='Price Action',
          )
      )
      fig.add_trace(
          go.Scatter(
              x=hist_df.index,
              y=hist_df['SMA_50'],
              line=dict(color='#ff9900', width=1.5),
              name='50 SMA',
          )
      )
      fig.add_trace(
          go.Scatter(
              x=hist_df.index,
              y=hist_df['SMA_200'],
              line=dict(color='#00ccff', width=1.5),
              name='200 SMA',
          )
      )
      fig.update_layout(
          title=f'{selected_stock_symbol} - Advanced Price Action & Moving Averages',
          xaxis_rangeslider_visible=False,
          height=500,
          template='plotly_dark',
      )
      st.plotly_chart(fig, use_container_width=True)

    with tab_fundamentals:
      col1, col2, col3, col4 = st.columns(4)
      col1.metric('Market Cap', stock_detail['Market Cap'])
      col2.metric('Price to Earnings (P/E)', stock_detail['P/E'])
      col3.metric('Return on Equity (ROE)', f"{stock_detail['ROE (%)']}%")
      col4.metric('Dividend Yield', f"{stock_detail['Div Yield (%)']}%")

      col5, col6, col7, col8 = st.columns(4)
      col5.metric('Price to Book (P/B)', stock_detail['P/B'])
      col6.metric('Debt to Equity', stock_detail['Debt/Eq'])
      col7.metric('Current RSI', stock_detail['RSI'])
      col8.metric('Sector', stock_detail['Sector'])

    with tab_ai:
      st.markdown(f'### 🤖 Automated Diagnostics for {selected_stock_symbol}')
      score_val = stock_detail['Score']

      if score_val >= 70:
        st.success(
            f'**Strong Profile (Score: {score_val}/100):** This stock shows'
            ' robust fundamental health and positive technical momentum.'
        )
      elif score_val >= 40:
        st.info(
            f'**Moderate Profile (Score: {score_val}/100):** Balanced metrics.'
            ' Some indicators look favorable while others require careful'
            ' monitoring.'
        )
      else:
        st.warning(
            f'**Cautious Profile (Score: {score_val}/100):** Higher risk or'
            ' weaker valuation metrics observed in current market conditions.'
        )

      st.markdown('**Key Highlights:**')
      for tag in stock_detail['Health Tags'].split(', '):
        st.markdown(f'- ✅ {tag}')
  else:
    st.info(
        'Click "Run Pro Market Scan" in the sidebar or main screen to load data.'
    )
