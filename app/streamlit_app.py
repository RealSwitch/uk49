import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import random

# Config
API_URL = os.environ.get('API_URL', 'http://localhost:8000')
st.set_page_config(page_title='UK49 Analytics Hub', layout='wide', initial_sidebar_state='expanded')

# Forensic analyst dark theme with accent colors
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #0b0f13;
    color: #cbd5e1;
}
.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    border-bottom: 2px solid rgba(0,209,178,0.3);
    margin-bottom: 20px;
}
.header-title {
    font-size: 32px;
    font-weight: 700;
    color: #00d1b2;
    margin: 0;
}
.kpi-card {
    background: linear-gradient(135deg, #0e1419 0%, #1a2332 100%);
    border: 1px solid rgba(0,209,178,0.2);
    border-radius: 8px;
    padding: 16px;
    text-align: center;
}
.kpi-value {
    font-size: 24px;
    font-weight: 700;
    color: #00d1b2;
    margin: 8px 0;
}
.kpi-label {
    font-size: 12px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.box {
    background: linear-gradient(180deg, #071018 0%, #0b1116 100%);
    border: 1px solid rgba(255,255,255,0.04);
    padding: 18px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(2,6,23,0.6);
    margin: 16px 0;
}
.section-title {
    font-size: 16px;
    font-weight: 600;
    color: #00d1b2;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 16px 0 12px 0;
    border-bottom: 1px solid rgba(0,209,178,0.2);
    padding-bottom: 8px;
}
.number-badge {
    display: inline-block;
    background: rgba(0,209,178,0.1);
    border: 1px solid rgba(0,209,178,0.3);
    color: #00d1b2;
    padding: 4px 10px;
    border-radius: 4px;
    margin: 4px 4px;
    font-weight: 600;
}
.hot { border-color: rgba(239,68,68,0.5); background: rgba(239,68,68,0.1); color: #ef4444; }
.cold { border-color: rgba(59,130,246,0.5); background: rgba(59,130,246,0.1); color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# ============ HEADER & EXPORT ============
col_title, col_export = st.columns([4, 1])
with col_title:
    st.markdown("<h1 class='header-title'>UK49 Analytics Hub</h1>", unsafe_allow_html=True)
with col_export:
    export_button = st.button('⬇️ Export Data')
    if export_button:
        st.session_state.show_export = True

# ============ DATA FETCHERS (CACHED) ============
@st.cache_data(ttl=300)
def fetch_draws():
    try:
        resp = requests.get(f"{API_URL}/draws?limit=1000", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data)
        if not df.empty:
            df['draw_date'] = pd.to_datetime(df['draw_date']).dt.date
        return df
    except Exception as e:
        st.error(f'Error fetching draws: {e}')
        return pd.DataFrame()


def compute_frequency(df: pd.DataFrame):
    if df.empty:
        return pd.DataFrame(columns=['number','count'])
    s = df['numbers'].str.split(',', expand=True)
    nums_list = []
    for col in s:
        nums_list.append(s[col].dropna().astype(int))
    nums = pd.concat(nums_list, ignore_index=True)
    freq = nums.value_counts().sort_index().reindex(range(1,50), fill_value=0).reset_index()
    freq.columns = ['number','count']
    return freq


def generate_candidates(freq_df: pd.DataFrame, method: str, k: int, candidates: int):
    results = []
    numbers = freq_df['number'].tolist()
    counts = freq_df['count'].tolist()
    total = sum(counts) if sum(counts)>0 else 1
    # weights
    if method == 'weighted_hot':
        weights = [c/total for c in counts]
    elif method == 'weighted_cold':
        inv = [ (max(counts)+1 - c) for c in counts]
        s = sum(inv)
        weights = [v/s for v in inv]
    elif method == 'top_hot':
        top = freq_df.sort_values('count', ascending=False).head(k)['number'].tolist()
        for _ in range(candidates):
            results.append(sorted(random.sample(top, k)))
        return results
    else:
        weights = None

    for _ in range(candidates):
        if weights:
            chosen = set()
            while len(chosen) < k:
                pick = random.choices(numbers, weights=weights, k=1)[0]
                chosen.add(pick)
            results.append(sorted(chosen))
        else:
            results.append(sorted(random.sample(numbers, k)))
    return results


# ============ SIDEBAR CONTROLS ============
with st.sidebar:
    st.header('🔧 Controls')
    start_date = st.date_input('Start date', value=(datetime.utcnow().date() - timedelta(days=90)))
    end_date = st.date_input('End date', value=datetime.utcnow().date())
    if start_date > end_date:
        st.error('Start date must be before end date')
    
    st.divider()
    st.subheader('Lucky Numbers')
    method = st.selectbox('Generation method', ['weighted_hot','weighted_cold','top_hot','random'])
    n_numbers = st.slider('Numbers per set', 1, 6, 6)
    n_candidates = st.number_input('Candidate sets', 1, 20, 5)

# ============ FETCH & PROCESS DATA ============
draws = fetch_draws()
if not draws.empty:
    draws_filtered = draws[(draws['draw_date'] >= start_date) & (draws['draw_date'] <= end_date)]
else:
    draws_filtered = pd.DataFrame()

freq_df = compute_frequency(draws_filtered)

# ============ KPI GRID ============
if not freq_df.empty:
    total_draws = len(draws_filtered)
    most_freq_num = int(freq_df.loc[freq_df['count'].idxmax(), 'number'])
    most_freq_count = int(freq_df['count'].max())
    least_freq_num = int(freq_df.loc[freq_df['count'].idxmin(), 'number'])
    avg_freq = freq_df['count'].mean()
else:
    total_draws = 0
    most_freq_num = '-'
    most_freq_count = 0
    least_freq_num = '-'
    avg_freq = 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Draws</div>
        <div class="kpi-value">{total_draws}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Most Frequent</div>
        <div class="kpi-value">{most_freq_num}</div>
        <div class="kpi-label">{most_freq_count} draws</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Least Frequent</div>
        <div class="kpi-value">{least_freq_num}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Avg Frequency</div>
        <div class="kpi-value">{avg_freq:.1f}</div>
    </div>
    """, unsafe_allow_html=True)

# ============ TWO-COLUMN LAYOUT ============
col_left, col_right = st.columns([2, 1], gap='medium')

# LEFT COLUMN: FREQUENCY CHART + DRAWS TABLE
with col_left:
    st.markdown("<div class='section-title'>📊 Frequency Chart</div>", unsafe_allow_html=True)
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    if not freq_df.empty:
        fig = px.bar(
            freq_df, x='number', y='count',
            labels={'count':'Frequency','number':'Number'},
            title=f'Number Frequency ({start_date} → {end_date})',
            color='count', color_continuous_scale='Plasma'
        )
        fig.update_layout(
            plot_bgcolor='#071018', paper_bgcolor='#071018',
            font_color='#cbd5e1', height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('No data available for selected date range')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>📋 Recent Draws</div>", unsafe_allow_html=True)
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    if not draws_filtered.empty:
        display_df = draws_filtered[['draw_date', 'numbers']].head(20).sort_values('draw_date', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info('No draws in selected date range')
    st.markdown("</div>", unsafe_allow_html=True)

# RIGHT COLUMN: LUCKY NUMBERS FORM + HOT/COLD NUMBERS
with col_right:
    st.markdown("<div class='section-title'>🎲 Lucky Numbers</div>", unsafe_allow_html=True)
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    if st.button('Generate', key='gen_btn', use_container_width=True):
        if freq_df.empty:
            st.warning('No data to generate from')
        else:
            candidates = generate_candidates(freq_df, method, n_numbers, n_candidates)
            st.session_state.candidates = candidates

    if 'candidates' in st.session_state:
        st.markdown('**Suggestions:**')
        for i, c in enumerate(st.session_state.candidates, 1):
            st.markdown(f'`{i}. ' + ' '.join(map(str, c)) + '`')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>🔥 Hot Numbers</div>", unsafe_allow_html=True)
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    if not freq_df.empty:
        hot = freq_df.sort_values('count', ascending=False).head(10)
        for idx, row in hot.iterrows():
            st.markdown(f'<span class="number-badge hot">{int(row["number"])}</span>', unsafe_allow_html=True)
    else:
        st.info('No data')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>❄️ Cold Numbers</div>", unsafe_allow_html=True)
    st.markdown("<div class='box'>", unsafe_allow_html=True)
    if not freq_df.empty:
        cold = freq_df.sort_values('count', ascending=True).head(10)
        for idx, row in cold.iterrows():
            st.markdown(f'<span class="number-badge cold">{int(row["number"])}</span>', unsafe_allow_html=True)
    else:
        st.info('No data')
    st.markdown("</div>", unsafe_allow_html=True)

# ============ EXPORT DATA ============
if st.session_state.get('show_export', False):
    st.divider()
    st.markdown("<div class='section-title'>📥 Export Data</div>", unsafe_allow_html=True)
    
    export_format = st.radio('Format:', ['CSV', 'JSON'], horizontal=True)
    
    if export_format == 'CSV':
        csv = freq_df.to_csv(index=False)
        st.download_button('📥 Download Frequency Data (CSV)', csv, 'uk49_frequency.csv', 'text/csv')
        
        draws_csv = draws_filtered[['draw_date', 'numbers']].to_csv(index=False)
        st.download_button('📥 Download Draws (CSV)', draws_csv, 'uk49_draws.csv', 'text/csv')
    else:
        json_freq = freq_df.to_json(orient='records')
        st.download_button('📥 Download Frequency Data (JSON)', json_freq, 'uk49_frequency.json', 'application/json')
        
        json_draws = draws_filtered[['draw_date', 'numbers']].to_json(orient='records', date_format='iso')
        st.download_button('📥 Download Draws (JSON)', json_draws, 'uk49_draws.json', 'application/json')

# ============ FOOTER ============
st.divider()
st.markdown(f"<div class='kpi-label'>Data range: {start_date} → {end_date}</div>", unsafe_allow_html=True)
