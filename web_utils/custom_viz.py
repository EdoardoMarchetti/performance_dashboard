import re
import streamlit as st
import numpy as np
import pandas as pd
from web_utils.data_manipulation import ensure_array
from web_utils.data_viz import DAY_IN_MS, create_bar_chart
import plotly_express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def create_bar_chart_overview(data, player, metrics_df, selected_metrics, selected_types, selected_dates, show_all_xaxes=True):

    df_melt = data.loc[((data.index == player) | 
                       (data.index == 'Team Average') ) &
                       (data.type.isin(selected_types)), 
                       selected_metrics+['date', 'type']]\
                        .reset_index()\
                        .melt(id_vars=['Player', 'date', 'type'], value_vars=selected_metrics, var_name='Metric')
    df_melt['date'] = df_melt['date'].astype(str)

    # Determine the min and max dates in the data
    min_date = pd.to_datetime(df_melt['date']).min()
    max_date = pd.to_datetime(df_melt['date']).max()

    # Ensure at least one week is displayed on the x-axis
    
    min_date = min_date - pd.Timedelta(days=3)
    max_date = max_date + pd.Timedelta(days=3)

    fig = px.bar(df_melt, x="date", y="value", 
                color="Player", facet_row="Metric", 
                barmode='overlay',
                text='value',
                category_orders={'Player': [ 'Team Average', player,]},
                facet_row_spacing=0.2*1/len(df_melt.Metric.unique()),
                hover_data={
                    'type':True,
                    'Player':False
                },
                hover_name='Player'
                )
    fig.update_yaxes(matches=None)
    fig.update_xaxes(showticklabels=True, range=[min_date, max_date])

    fig.for_each_annotation(lambda a: a.update(
        text=f"<span style='color:black';>{a.text.split('=')[-1]}</span>",
        x=-0.05,  # Adjust the x position to move the annotation to the left
        xref="paper"
        ))



    for trace in fig.data:
        
        match = re.search(r'Metric=([^<]+)<br>', trace.hovertemplate)
        if match:
            metric = match.group(1)
            color = np.array(metrics_df.loc[metrics_df.name==metric, 'color'].iloc[0])*255
            
        if trace.name == player:
            trace.width = DAY_IN_MS * 0.6 # Set the width of bars for 'Team Average'
            trace.marker = dict(color=f"rgb{tuple(color)}", opacity=0.4)
            trace.textfont = dict(color='black')
            trace.name = f'{player}'
        else:
            trace.width = DAY_IN_MS * 0.2 # Set the width of bars for player 'A'
            trace.marker = dict(color=f"white", opacity = 0.2, line=dict(width=2, ))
            trace.text = ''
            trace.hovertemplate = trace.hovertemplate.replace('value=%{text}', 'value=%{y}')
            trace.name = f'Team average'
            
            
    title = f'{player} | Overview '
    subtitle = f"{','.join(selected_types)}| From {selected_dates[0]}"
    if len(selected_dates) > 1:
        subtitle += f' To {selected_dates[1]}'

    title = title + "<br><sup style='color: gray'>"+subtitle+'</sup>'

    
    fig.update_layout(
        showlegend=False,
        height = 300*len(selected_metrics) if len(selected_metrics) > 2 else 500,
        title = dict(text=title, pad=dict(l=50), xanchor='left', font=dict(size=20)),
        margin = dict(l=50, r=50, b=50),
    )

    for i in range(1, len(selected_metrics) + 1):
        fig.layout[f'yaxis{i}'].title.text = ''

    for i, m in enumerate(selected_metrics):
        player_avg = data.loc[player, m].mean()

        fig.add_hline(y=player_avg, row=len(selected_metrics)-i, col=1, line_dash="dot",
                    line_color='red',
                    opacity=0.4,
                    annotation = dict(text=f'{round(player_avg, 2)}', align= "right"),
                    layer='below',
                    showlegend=True if i == 0 else False,
                    name=f'{player} average'
                    )
    
        
    return fig


def create_divergent_bar_chart(data, dates, player, col_left, col_right, session_type):


    
    
    value_left = ensure_array(data.loc[player, col_left])
    if len(value_left.shape)>1:
        value_left = np.squeeze(value_left).sum(axis=0)
    
    
    value_right = ensure_array(data.loc[player, col_right])
    if len(value_right.shape)>1:
        value_right = np.squeeze(value_right).sum(axis=0)


    max_val = abs(np.array([value_left, value_right])).max()

    bar_labels_pos = list(range(5))
    bar_labels_names_acc = ['1-2 m/s2', '2-3 m/s2', '3-4 m/s2', '> 4 m/s2', '> 5 m/s2']
    bar_labels_names_dec = ['-2 & -1 m/s2', '-3 & -2 m/s2', '-4 & -3 m/s2', '< -4 m/s2', '< -5 m/s2']
    fig = create_bar_chart(labels=bar_labels_pos,
                            values=value_left, wrap_label=False, 
                            bar_width=0.5
                            )
    
    fig = create_bar_chart(labels=bar_labels_pos,
                                values=value_right*-1, barmode = 'relative', fig = fig,  wrap_label=False,
                                bar_width=0.5)
    
    padding = 0.2*max_val
    for i, a, d in list(zip(bar_labels_pos, bar_labels_names_acc, bar_labels_names_dec)):
        fig.add_annotation(
            x=max_val+padding, y=i,
            text=a,
            showarrow=False,
            font=dict(
            size=12,
            color="Black"
            ),
        )

        fig.add_annotation(
            x=-(max_val+padding), y=i,
            text=d,
            showarrow=False,
            font=dict(
            size=12,
            color="Black"
            ),
        )

    
    

    # Create custom tick labels (convert to positive)
    custom_tickvals = np.linspace(-(max_val*0.80), (max_val*0.80), 9)
    custom_ticktext = [str(abs(int(val))) for val in custom_tickvals]

    
    
    fig.update_layout(
        yaxis = dict(autorange='reversed',showticklabels=False),
        xaxis = dict(range=[-(padding+max_val), max_val+padding], 
                    showgrid=True,
                    tickvals=custom_tickvals,
                    ticktext=custom_ticktext
                    ),
        showlegend=False,
        margin = dict(l=50,r=50, b=50),
    )

    for trace_left, trace_rigth in zip(fig.data[1::2], fig.data[::2]):
            
            modified_x_left = [-x for x in trace_left.x]
            trace_left.customdata = list(zip(bar_labels_names_dec, modified_x_left))
            trace_rigth.customdata = list(zip(bar_labels_names_acc))


            trace_left.hovertemplate = (
                '<span style="color: black;">%{customdata[0]}</span>: %{customdata[1]}'
            )

            trace_rigth.hovertemplate = (
                '<span style="color: black;">%{customdata[0]}</span>: %{x}'
            )

    return fig


def create_session_bar_overview(data, metrics_df, selected_metrics, session_type, session_date, sort_by='Metric', horizontal = True):

    n_metrics = len(selected_metrics)
    n_cols = 2
    n_rows = (n_metrics + 1) // n_cols  # This ensures the number of rows needed


    fig = make_subplots(rows=n_rows, cols=n_cols, subplot_titles=selected_metrics, vertical_spacing=0.15)
    players_data = data.loc[data.Player != 'Team Average']
    team_avg_data = data.loc[data.Player == 'Team Average']

    for i, metric in enumerate(selected_metrics):
        col = (i % n_cols) +1
        row = (i // n_cols) + 1  # Corrected to use n_cols
        color = tuple(np.array(metrics_df.loc[metrics_df.name==metric, 'color'].values[0])*255)
        subplot_data = players_data[['Player', metric]].sort_values(
            by= metric if sort_by == 'Metric' else 'Player',
            ascending = horizontal
        )
        avg_value = players_data[metric].mean()
        
        custom_data = []
        for val in subplot_data[metric]:
            ratio = (1 - val / avg_value) * -100
            if ratio < 0:
                formatted_ratio = f"<span style='color:red;'>▼ {ratio:.2f}%  </span>"
            else:
                formatted_ratio = f"<span style='color:green;'>▲ {ratio:.2f}%  </span>"
            custom_data.append(formatted_ratio)
        

        if horizontal:
            x = subplot_data[metric]
            y = subplot_data['Player']
            orientation = 'h'
            hovertemplate = '<span style="font-size: larger; color: black;">%{y}: %{x}</span><br>%{customdata}'
        else:
            x = subplot_data['Player']
            y = subplot_data[metric]
            orientation = 'v'
            hovertemplate = '<span style="font-size: larger; color: black;">%{x}: %{y}</span><br>%{customdata}'
        
        fig.add_trace(
            go.Bar(
                x=x,
                y=y,
                orientation=orientation,
                marker=dict(color=f"rgb{color}"),
                name=metric,
                customdata=custom_data,  # Pass the precomputed custom_data list
                hovertemplate=hovertemplate,
                text=subplot_data[metric],
                textfont=dict(size=12)
            ),
            row=row,
            col=col
        )
        
        if horizontal:
            fig.add_vline(
                    row=row,
                    col=col,
                    x=avg_value,
                    line_color = 'red',
                    annotation_text=round(avg_value,2),
                    annotation_position='bottom right',
                    annotation_font_color="red")
        
        else:
            fig.add_hline(
                    row=row,
                    col=col,
                    y=avg_value,
                    line_color = 'red',
                    annotation_text=round(avg_value,2),
                    annotation_position='bottom right',
                    annotation_font_color="red")
        
        
    title = 'Session overview'
    subtitle = f'{session_type} | {session_date} | Average value in red'
    title += "<br><sup style='color: gray'>"+subtitle+"<sup>"
    fig.update_layout(
        title = dict(text=title, pad=dict(l=50), xanchor='left', font=dict(size=20)),
        height = 500 * n_rows,
        showlegend=False,
        margin = dict(l=50, r=50, b=50),
    )

    fig.update_traces(textangle=0)


    return fig
