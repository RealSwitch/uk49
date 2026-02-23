

# ============ STREAMLIT UI ============
if __name__ == "__main__":
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px

    # ============ SIDEBAR CONTROLS ============
    with st.sidebar:
        st.header('🔧 Controls')
        start_date = st.date_input('Start date', value=(datetime.utcnow().date() - timedelta(days=90)))
        end_date = st.date_input('End date', value=datetime.utcnow().date())
        if start_date > end_date:
            st.error('Start date must be before end date')
        st.divider()
        st.subheader('Draw Type')
        draw_type = st.selectbox('Filter by draw type', ['All', 'lunchtime', 'teatime'])
        st.divider()
        st.subheader('Lucky Numbers')
        method = st.selectbox('Generation method', ['weighted_hot','weighted_cold','top_hot','random'])
        n_numbers = st.slider('Numbers per set', 1, 6, 6)
        n_candidates = st.number_input('Candidate sets', 1, 20, 5)

    # ============ FETCH & PROCESS DATA ============
    draws = fetch_draws()
    if not draws.empty:
        draws_filtered = draws[(draws['draw_date'] >= start_date) & (draws['draw_date'] <= end_date)]
        # Filter by draw type if specified
        if draw_type != 'All':
            draws_filtered = draws_filtered[draws_filtered.get('draw_type', 'lunchtime') == draw_type]
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
            type_label = f" ({draw_type})" if draw_type != 'All' else " (All)"
            fig = px.bar(
                freq_df, x='number', y='count',
                labels={'count':'Frequency','number':'Number'},
                title=f'Number Frequency {type_label}: {start_date} → {end_date}',
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
            # Show draw_type if available
            if 'draw_type' in draws_filtered.columns:
                display_df = draws_filtered[['draw_date', 'draw_type', 'numbers']].head(20).sort_values('draw_date', ascending=False)
            else:
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
draws = fetch_draws()
if not draws.empty:
    draws_filtered = draws[(draws['draw_date'] >= start_date) & (draws['draw_date'] <= end_date)]
    # Filter by draw type if specified
    if draw_type != 'All':
        draws_filtered = draws_filtered[draws_filtered.get('draw_type', 'lunchtime') == draw_type]
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
        type_label = f" ({draw_type})" if draw_type != 'All' else " (All)"
        fig = px.bar(
            freq_df, x='number', y='count',
            labels={'count':'Frequency','number':'Number'},
            title=f'Number Frequency {type_label}: {start_date} → {end_date}',
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
        # Show draw_type if available
        if 'draw_type' in draws_filtered.columns:
            display_df = draws_filtered[['draw_date', 'draw_type', 'numbers']].head(20).sort_values('draw_date', ascending=False)
        else:
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
