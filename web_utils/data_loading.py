import json
import os
from sqlalchemy import create_engine
from database_operations.sql_queries import *


import os.path as osp

import streamlit as st


def get_engine(db_path=osp.join('data', 'spezia_22_23.db')):
    engine = create_engine(f'sqlite:///{db_path}', echo=False)

    return engine

@st.cache_data
def load_files(db_path):
    df = select_from(engine=get_engine(db_path),
                       from_table='file_available',
                       )
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d').dt.date
    return df

@st.cache_data
def load_stats(db_path, dates, types, category):
    where_condition = ""

    if dates:
        # Build the date condition
        where_condition = f"date >= '{dates[0]}'"
        if len(dates) > 1:
            where_condition += f" AND date <= '{dates[1]}'"

    # Build the type list condition
    if types:
        if where_condition:
            where_condition += ' AND'
        types_str = ", ".join(f"'{t}'" for t in types)
        where_condition += f" type IN ({types_str})"

    if category:
        if where_condition:
            where_condition += ' AND'
        where_condition += f" category = '{category}'"

    print(where_condition)

    return select_from(engine=get_engine(db_path), 
                from_table='stats',
                where_condition=where_condition)


@st.cache_data
def load_metrics():
    with open(osp.join('glossaries', 'metrics.json')) as f:
        return json.load(f)
    
