import streamlit as st
import os.path as osp

from web_utils.connection import GoogleDriveManager

pages = {
    "Performance reports" : [
        st.Page("pages_script/player_report.py", title="Player Report", icon="🏃"),
        st.Page("pages_script/session_report.py", title="Session Report", icon="🏋🏿‍♂️")
    ],
}

pg = st.navigation(pages)

if not 'local_save_path' in st.session_state:
    st.session_state['local_save_path'] = osp.join('data','gps_data_new.db')

pg.run()