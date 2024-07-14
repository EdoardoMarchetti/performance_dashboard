import streamlit as st
import pandas as pd
import numpy as np
import os 
import os.path as osp
import plotly_express as px
import plotly

from streamlit_extras.stylable_container import stylable_container

from web_utils.custom_viz import create_session_bar_overview
from web_utils.data_loading import *
from web_utils.styles import *


st.set_page_config(page_title="Session Report", 
                   page_icon="🏋🏿‍♂️", 
                   layout="wide")


st.markdown('# Session Report')
st.markdown('Use the sidebar to select the session')



file_available = load_files(st.session_state['local_save_path'])

#MARK: Sidebar
st.sidebar.markdown("# Filters")
selected_category = st.sidebar.selectbox(label='Select cateogry',
                                options = file_available.category.unique())
session_type = st.sidebar.selectbox(label="Session type",
                     options = file_available.loc[file_available.category == selected_category, 'type'].unique())
session_date = st.sidebar.selectbox(label="Select session date (yyyy-mm-dd)",
              options=file_available.loc[(file_available.category == selected_category) & (file_available.type == session_type), 'date'].unique())

if st.sidebar.button('Update data'):
    load_files.clear()
    load_stats.clear()
    st.rerun()

#MARK: Load the data
session_data = load_stats(
    db_path=st.session_state['local_save_path'],
    dates = [session_date]*2,
    types= [session_type],
    category=selected_category
)

metrics = load_metrics()
metrics_df = pd.DataFrame(metrics)
metrics_names = [m['name'] for m in metrics]

#MARK: Session stats
with stylable_container(key = f'session_overview_kpi', css_styles = "div[data-testid='stMetric']{"+shadow_effect_kpi+"}"):       
    
    presence_col, duration_col = st.columns(2, gap = 'large', vertical_alignment = 'center')

    with presence_col:
        st.metric(
                label=f'Players involved',
                value=len(session_data)-1,
            )
    with duration_col:
        st.metric(
            label='Total session time (minutes)',
            value = session_data.Minutes.max(),
        )

st.divider()

#MARK: session overview
overview_selectors = st.columns([0.5,0.3,0.3], gap='large', vertical_alignment = 'center' )
with overview_selectors[0]:
    selected_metrics = st.multiselect(label='Select metrics',
                options = metrics_names,
                default = metrics_names[0])
with overview_selectors[1]:
    sort_by = st.radio(
        label='Sort by',
        horizontal = True,
        options = ['Metric', 'Player']
    )
with overview_selectors[2]:
    orientation = st.radio(
        label='Orientation',
        horizontal = True,
        options = ['Vertical','Horizontal'],
        index = 0
    )

if len(selected_metrics) == 0:
    st.warning('Please select at least a metric')
    st.stop()

fig = create_session_bar_overview(
    data = session_data,
    metrics_df=metrics_df,
    selected_metrics=selected_metrics,
    session_type=session_type,
    session_date=session_date,
    sort_by=sort_by,
    horizontal = True if orientation == 'Horizontal' else False,
)

with stylable_container(key = f'session_overview_graph', css_styles = ["""
                                    .stPlotlyChart{
                                        margin-bottom: 50px;
                                    }""",
                                    f"""
                                    .main-svg{{{ 
                                    shadow_effect_graph
                                    }}}
                                    """]):
                st.plotly_chart(fig, use_container_width = True)
    



