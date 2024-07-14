import re
import streamlit as st
from web_utils.colors import VELOCITIES_INTERVAL
from web_utils.data_loading import *
from datetime import datetime

from web_utils.data_manipulation import convert_to_seconds, ensure_array, ensure_list, filter_velocities, sort_vel_intervals, sum_time_columns
from web_utils.data_viz import *
from web_utils.styles import *
from web_utils.custom_viz import *
from web_utils.connection import GoogleDriveManager
from streamlit_extras.stylable_container import stylable_container

st.set_page_config(page_title="Performance Dashboard", 
                   page_icon="📈", 
                   layout="wide")


st.markdown('# Performance Dasboard')
st.markdown('Use the sidebar to select dates and player')




# MARK: Selectors
file_available = load_files(st.session_state['local_save_path'])

min_date = file_available.date.min() #Data iniziale minima
max_date = file_available.date.max() #Data iniziale massima

st.sidebar.markdown('# Filters')

dates = st.sidebar.date_input(label="Select day interval",
                             value = [min_date, max_date])

#Filtra la tabella in base alle date scelte
if len(dates) == 0:
    st.warning('Please select a time interval')
    st.stop()
elif len(dates) == 1:
    file_available = file_available.loc[file_available.date >= dates[0]]
else :
    file_available = file_available.loc[(file_available.date >= dates[0]) & (file_available.date <= dates[1])]


# #MARK: Caricamento dati
data = load_stats(st.session_state['local_save_path'], dates=dates, types=[], category='')
data.set_index('Player', inplace=True)
metrics_dict = load_metrics()
metrics_df = pd.DataFrame(metrics_dict)
metrics_names = [m['name'] for m in metrics_dict]

player = st.sidebar.selectbox(label='Select player', options = data.index.unique())



# #MARK: Overview
selected_types = st.multiselect(label='Select session types',
        options = list(data.type.unique()),
        default = list(data.type.unique()))

selected_metrics = st.multiselect(label='Select metrics',
        options = list(data.columns),
        default = list(data.columns)[0])


if len(selected_metrics) > 0:
    fig = create_bar_chart_overview(
        data=data,
        player=player,
        metrics_df=metrics_df,
        selected_metrics=selected_metrics,
        selected_types=selected_types,
        selected_dates=dates,
        show_all_xaxes=True
    )

    fig.update_layout(
        showlegend = True
    )

    with stylable_container(key = f'overview', css_styles = ["""
                                        .stPlotlyChart{
                                            margin-bottom: 50px;
                                        }""",
                                        f"""
                                        .main-svg{{{ 
                                        shadow_effect_graph
                                        }}}
                                        """]): 
        st.plotly_chart(fig, use_container_width = True)
else:
    st.warning('Select a metric')

st.divider()
#MARK: Metric Detail
st.markdown('## Metric Detail')

metrics = st.multiselect(label='Seleziona metriche',
            options = list(data.columns),
            default = selected_metrics)
    
training_col, match_col = st.columns([0.5,0.5], gap="large")

training_data = data.loc[data.type == 'Full Training']
match_data = data.loc[data.type == 'Full Match']
warns = {t:0 for t in ['Full Training', 'Full Match']}
for idx, metric in enumerate(metrics):
    for type, type_data, col in list(zip(['Full Training', 'Full Match'], [training_data, match_data] ,[training_col, match_col])):
        with col:
            if (len(type_data) == 0 and not warns[type]):
                st.warning(f'Not {type} session for this time interval')
                warns[type] = 1
                continue
            if warns[type]:
                continue
            
            labels = ensure_array(type_data.loc[player, 'date'])
            inner_values = ensure_array(type_data.loc['Team Average', metric])
            inner_minutes = ensure_array(type_data.loc['Team Average', 'Minutes'])
            outer_values = ensure_array(type_data.loc[player, metric])
            outer_times = ensure_array(type_data.loc[player, 'Minutes'])
            
            st.markdown(f"<h3 style='text-align: center; color: black;'> {type} - {metric} </h3>", unsafe_allow_html=True)
            
            if len(labels) == 0:
                st.warning(f'No {type} session available for the given time interval')
                continue
            

            with stylable_container(key = f'kpi_col_{str(idx)}_{type.split()[1]}', css_styles = "div[data-testid='stMetric']{"+shadow_effect_kpi+"}"):
                
                kpis = st.columns(2)

            with kpis[0]:
                st.metric(
                label=f'Totale {metric}',
                value=round(sum(outer_values), 2),
                delta=f"{round((1-sum(outer_values)/sum(inner_values))*-100, 2)}%",
                help='Il delta indica come ha performato rispetto alla media di squadra in %'
            )
                
            with kpis[1]:
                st.metric(
                    label=f'Media x sessione {metric}',
                    value=round(np.array(outer_values).mean(), 2),
                    delta=f"{round(((np.array(inner_values)-np.array(outer_values)) / np.array(inner_values)*-100).mean(), 2)}%",
                    help='Il delta indica come ha performato in media per sessione rispetto alla media di squadra in %'
                )

            

            fig = create_bar_chart(labels=labels,
                            values=inner_values,
                            orientation='v',
                            color='rgba(0,0,0,0.2)',
                            bar_width=DAY_IN_MS*0.1, 
                            trace_name='Session team average',
                            wrap_label=False
                            )

            fig = create_bar_chart(labels=labels,
                                values=outer_values,
                                orientation='v',
                                color='white',
                                bar_width=DAY_IN_MS*0.6,
                                text=outer_values,
                                trace_name=player,
                                fig = fig,
                                barmode='overlay',
                                wrap_label=False
                                )
            
            

            fig.add_shape(
                type='line',
                x0 = 0.01,
                x1 = 1.05,
                y0 = outer_values.mean(),
                y1 = outer_values.mean(),
                label=dict(text=round(outer_values.mean(),2), xanchor='right', textposition="end", 
                           font=dict(color='red')),
                xref ='paper',
                line=dict(color='Red',dash="dashdot"),
                showlegend=True,
                name=f'{player} average'
            )
            
            title = f'{player} - {metric}'
            subtitle = f'{type} | From {dates[0]}'
            if len(dates) > 1:
                subtitle += f' To {dates[1]}'

            title = title + "<br><sup style='color: gray'>"+subtitle+'</sup>'

            if len(labels) > 1:
                min_date, max_date = labels.min(), labels.max()
            else:
                min_date, max_date = labels[0], labels[0]
            min_date = datetime.strptime(min_date, '%Y-%m-%d')
            max_date = datetime.strptime(max_date, '%Y-%m-%d')
            
            

            fig.update_layout(
                showlegend = True,
                title = dict(text=title, pad=dict(l=50), xanchor='left', font=dict(size=20)),
                margin = dict(l=50, r=50, b=50),
                legend=dict(
                    orientation='h',
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="right",
                    x=1),
            )

            pad = pd.Timedelta(days=2)
            fig.update_xaxes(showticklabels=True, 
                             range=[min_date-pad, max_date+pad])

            # Combine tooltips to show both outer and inner values
            for trace_outer, trace_inner in zip(fig.data[1::2], fig.data[0::2]):
                trace_outer.customdata = list(zip(labels, inner_values, outer_times, inner_minutes))
                trace_inner.customdata = list(zip(labels, outer_values, outer_times, inner_minutes))

                trace_outer.hovertemplate = (
                    'Date: %{customdata[0]}  <br>' +
                    '<span style="font-size: larger; color: black;">' + f'{player}: %{{y}} |</span> Minutes: %{{customdata[2]}}<br>' +
                    '<span style="font-size: larger; color: black;">' + 'Team Average: %{customdata[1]} |</span> Minutes: %{customdata[3]}<extra></extra>'
                )

                trace_outer.marker = dict(
                    color='rgba(252,168,3, 0.5)',  opacity=0.6
                    )

                #trace_outer.textposition = 'outside'

                trace_inner.hovertemplate = (
                    'Date: %{customdata[0]}<br>' +
                    '<span style="font-size: larger; color: black;">' + f'{player}: %{{customdata[1]}} |</span>  Minutes: %{{customdata[2]}}<br>' +
                    '<span style="font-size: larger; color: black;">' + 'Team Average: %{y} |</span> Minutes: %{customdata[3]} <extra></extra>'
                )

                trace_inner.marker = dict(
                    dict(color=f"white", opacity = 0.2, line=dict(width=2, ))
                )

            with stylable_container(key = f'graph_col_{str(idx)}', css_styles = ["""
                                    .stPlotlyChart{
                                        margin-bottom: 50px;
                                    }""",
                                    f"""
                                    .main-svg{{{ 
                                    shadow_effect_graph
                                    }}}
                                    """]):
                st.plotly_chart(fig, use_container_width = True)



st.divider()

# MARK: Analisi Accelerazioni/Decelerazioni
st.markdown("## Analisi Accelerazioni e decelerazioni")
training_col, match_col = st.columns([0.5,0.5], gap='large')
warns = {t:0 for t in ['Full Training', 'Full Match']}
for col, t_data, t in zip([training_col, match_col], [training_data, match_data], ['Full Training', 'Full Match']):
    with col:
        if (len(t_data) == 0 and not warns[t]):
                st.warning(f'Not {t} session for this time interval')
                warns[t] = 1
                continue
        if warns[t]:
            continue

        fig = create_divergent_bar_chart(t_data, dates, player, 
                                    col_left=['D acc 1-2 m/s2',
                                                'D acc 2-3 m/s2', 
                                                'D acc 3-4 m/s2', 
                                                'D acc > 4 m/s2', 
                                                'D acc > 5 m/s2',], 
                                    col_right = ['D dec -2 & -1 m/s2',
                                                'D dec -3 & -2 m/s2', 
                                                'D dec -4 & -3 m/s2',
                                                'D dec < -4 m/s2',
                                                'D dec < -5 m/s2'] , 
                                    session_type=t)


        title = "Analisi <span style='color:#83c9ff';>Decelerazioni</span> e <span style='color:#0068c9';>Accelerazioni</span>"
    
        subtitle = f'{t} | Distanza percorsa | From {dates[0]}'
        if len(dates) > 1:
            subtitle += f' To {dates[1]}'
        title +=  "<br><sup style='color: gray'>"+subtitle+'</sup>'

        fig.update_layout(title = dict(text=title, pad=dict(l=50), xanchor='left', font=dict(size=20)),)

        
        with stylable_container(key = f'graph_col_test', css_styles = ["""
                                    .stPlotlyChart{
                                        margin-bottom: 50px;
                                    }""",
                                    f"""
                                    .main-svg{{{ 
                                    shadow_effect_graph
                                    }}}
                                    """]):
            st.plotly_chart(fig, use_container_width = True)

        fig = create_divergent_bar_chart(t_data, dates, player, 
                                    col_left=['T acc 1-2 m/s2',
        'T acc 2-3 m/s2', 'T acc 3-4 m/s2', 'T acc > 4 m/s2', 'T acc > 5 m/s2',], 
                                    col_right = ['T dec -2 & -1 m/s2',
                                        'T dec -3 & -2 m/s2', 
                                        'T dec -4 & -3 m/s2',
                                        'T dec < -4 m/s2',
                                        'T dec < -5 m/s2'] , 
                                    session_type=t)
        
        title = "Analisi <span style='color:#83c9ff';>Decelerazioni</span> e <span style='color:#0068c9';>Accelerazioni</span>"
    
        subtitle = f'{t} | Tempo | From {dates[0]}'
        if len(dates) > 1:
            subtitle += f' To {dates[1]}'
        title +=  "<br><sup style='color: gray'>"+subtitle+'</sup>'

        fig.update_layout(title = dict(text=title, pad=dict(l=50), xanchor='left', font=dict(size=20)),)
        
        with stylable_container(key = f'graph_col_test', css_styles = ["""
                                    .stPlotlyChart{
                                        margin-bottom: 50px;
                                    }""",
                                    f"""
                                    .main-svg{{{ 
                                    shadow_effect_graph
                                    }}}
                                    """]):
            st.plotly_chart(fig, use_container_width = True)





# MARK: Analisi Velocità
st.divider()
st.markdown("## Analisi Velocità")
vel_intervals = st.multiselect(label='Select velocity intervals', options = VELOCITIES_INTERVAL.keys(), default = VELOCITIES_INTERVAL.keys())

if len(vel_intervals) == 0:
    st.warning('Please select at least an interval')
else:
    training_col, match_col = st.columns([0.5,0.5], gap='large')

    velocities_distance = ['Dist 0-5 km/h',
        'Dist 5-10 km/h', 'Dist 10-15 km/h', 'Dist 15-20 km/h',
        'Dist 20-25 km/h', 'Dist > 25 km/h',]



    velocities_temp = [
        'T 0-5 km/h', 'T 5-10 km/h',
        'T 10-15 km/h', 'T 15-20 km/h', 'T 20-25 km/h',
        'T>25 km/h',
    ]

    vel_intervals = sort_vel_intervals(vel_intervals)

    velocities_distance, velocities_temp = filter_velocities(vel_intervals, velocities_distance, velocities_temp)
    warns = {t:0 for t in ['Full Training', 'Full Match']}
    for col, t_data, t in zip([training_col, match_col], [training_data, match_data], ['Full Training', 'Full Match']):

        with col:
            if (len(t_data) == 0 and not warns[t]):
                st.warning(f'Not {t} session for this time interval')
                warns[t] = 1
                continue
            if warns[t] == 1:
                continue

            labels = ensure_array(t_data.loc[player, 'date'])

            if len(labels) > 1:
                min_date, max_date = labels.min(), labels.max()
            else:
                min_date, max_date = labels[0], labels[0]
            min_date = datetime.strptime(min_date, '%Y-%m-%d')
            max_date = datetime.strptime(max_date, '%Y-%m-%d')

            fig = None
            for vel_c, v_int in zip(velocities_distance, vel_intervals):
                fig = create_bar_chart(
                    labels=labels,
                    values=ensure_array(t_data.loc[player, vel_c]),
                    color=VELOCITIES_INTERVAL[v_int],
                    orientation='v',
                    barmode='stack',
                    fig = fig,
                    trace_name=vel_c,
                    wrap_label=False,
                    bar_width=DAY_IN_MS*0.8
                )

            title = 'Analisi Velocità'
            subtitle = f'{t} | Distanza | From {dates[0]}'
            if len(dates) > 1:
                subtitle += f' To {dates[1]}'
            title +=  "<br><sup style='color: gray'>"+subtitle+'</sup>'


            fig.update_layout(margin = dict(l=50, r=50, b=50),
                            legend=dict(
                                orientation='h',
                                yanchor="bottom",
                                y=-0.3,
                                xanchor="right",
                                x=1,
                                traceorder="normal",
                                ),
                                title = dict(text=title, x = 0.08, xanchor='left', font=dict(size=20)),
                                showlegend=True,)
            
            pad = pd.Timedelta(days=2)
            fig.update_xaxes(showticklabels=True, 
                             range=[min_date-pad, max_date+pad])

            with stylable_container(key = f'graph_col_dist_{t.split()[-1]}', css_styles = ["""
                                        .stPlotlyChart{
                                            margin-bottom: 50px;
                                        }""",
                                        f"""
                                        .main-svg{{{ 
                                        shadow_effect_graph
                                        }}}
                                        """]):
                st.plotly_chart(fig, use_container_width = True)



            fig = None
            for vel_c, v_int in zip(velocities_temp, vel_intervals):
                fig = create_bar_chart(
                    labels=labels,
                    values=ensure_array(t_data.loc[player, vel_c]),
                    color=VELOCITIES_INTERVAL[v_int],
                    orientation='v',
                    barmode='stack',
                    fig = fig,
                    trace_name=vel_c,
                    wrap_label=False,
                    bar_width=DAY_IN_MS*0.8
                )

            title = 'Analisi Velocità'
            subtitle = f'{t} | Tempo | From {dates[0]}'
            if len(dates) > 1:
                subtitle += f' To {dates[1]}'
            title +=  "<br><sup style='color: gray'>"+subtitle+'</sup>'

            fig.update_layout(margin = dict(l=50, r=50, b=50),
                            legend=dict(
                                orientation='h',
                                yanchor="bottom",
                                y=-0.3,
                                xanchor="right",
                                x=1,
                                traceorder="normal",
                                ),
                                title = dict(text=title, xanchor='left', font=dict(size=20), x = 0.08),
                                showlegend=True,)
            
            pad = pd.Timedelta(days=2)
            fig.update_xaxes(showticklabels=True, 
                             range=[min_date-pad, max_date+pad])
            with stylable_container(key = f'graph_col_temp_{t.split()[-1]}', css_styles = ["""
                                        .stPlotlyChart{
                                            margin-bottom: 50px;
                                        }""",
                                        f"""
                                        .main-svg{{{ 
                                        shadow_effect_graph
                                        }}}
                                        """]):
                st.plotly_chart(fig, use_container_width = True)

        
    
    


        
        

            



    







