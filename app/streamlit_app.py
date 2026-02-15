import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

# Get API URL from environment variable or use default
API_URL = os.environ.get('API_URL', 'http://api:8000')

st.set_page_config(page_title='UK49 Analytics', layout='wide')
st.title('🎰 UK49 Lottery Analytics')

# Section: Recent Draws
with st.expander('📊 Recent Draws', expanded=False):
    try:
        resp = requests.get(f"{API_URL}/draws", timeout=5)
        resp.raise_for_status()
        draws = resp.json()
        if draws:
            draws_df = pd.DataFrame(draws)
            st.dataframe(draws_df, use_container_width=True)
        else:
            st.info('No draws available')
    except Exception as e:
        st.error(f'Could not fetch draws: {e}')

# Section: Hot Numbers (Top 10)
st.subheader('🔥 Top 10 Hot Numbers (Last 30 Days)')
try:
    resp = requests.get(f"{API_URL}/stats/hot_numbers?top_n=10", timeout=5)
    resp.raise_for_status()
    hot_data = resp.json()
    draw_date = hot_data.get('draw_date', 'N/A')
    hot_nums = hot_data.get('hot_numbers', [])
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if hot_nums:
            fig = px.bar(
                x=[str(h['number']) for h in hot_nums],
                y=[h['freq_30d'] for h in hot_nums],
                labels={'x': 'Number', 'y': 'Frequency (30d)'},
                title=f'Top 10 Numbers - {draw_date}'
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('### Rankings')
        for rank, h in enumerate(hot_nums, 1):
            st.metric(f"#{rank}", f"Number {h['number']}", f"{h['freq_30d']} draws")
except Exception as e:
    st.error(f'Could not fetch hot numbers: {e}')

# Section: Rolling Frequency Heatmap
st.subheader('📈 Rolling Frequency Heatmap (Last 30 Days)')
try:
    resp = requests.get(f"{API_URL}/stats/rolling_frequency", timeout=5)
    resp.raise_for_status()
    freq_data = resp.json()
    draw_date = freq_data.get('draw_date', 'N/A')
    frequencies = freq_data.get('frequencies', [])
    
    if frequencies:
        freq_df = pd.DataFrame(frequencies)
        freq_df = freq_df.sort_values('number')
        
        fig = go.Figure(data=go.Heatmap(
            z=[freq_df['freq_30d'].values],
            x=freq_df['number'].astype(str),
            y=['Frequency'],
            colorscale='YlOrRd',
            hovertemplate='Number: %{x}<br>Frequency (30d): %{z}<extra></extra>'
        ))
        fig.update_layout(
            title=f'Number Frequency Heatmap - {draw_date}',
            xaxis_title='Number',
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('No frequency data available')
except Exception as e:
    st.error(f'Could not fetch frequency data: {e}')

# Section: Full Frequency Distribution
st.subheader('📊 Full Frequency Distribution (All 49 Numbers)')
try:
    resp = requests.get(f"{API_URL}/stats/rolling_frequency", timeout=5)
    resp.raise_for_status()
    freq_data = resp.json()
    frequencies = freq_data.get('frequencies', [])
    
    if frequencies:
        freq_df = pd.DataFrame(frequencies).sort_values('freq_30d', ascending=False)
        
        fig = px.bar(
            freq_df,
            x='number',
            y='freq_30d',
            labels={'number': 'Number', 'freq_30d': 'Frequency (30d)'},
            title='All Numbers - 30-Day Rolling Frequency',
            color='freq_30d',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('No frequency data available')
except Exception as e:
    st.error(f'Could not fetch frequency distribution: {e}')

st.markdown('---')
st.caption(f'Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
