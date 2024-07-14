import pandas as pd
import plotly as pt
import plotly.graph_objects as go
import plotly_express as px

#from data.roles import position_dict

from matplotlib import cm, pyplot as plt, ticker
import matplotlib.patheffects as path_effects
from mplsoccer import PyPizza, add_image, FontManager, Pitch, VerticalPitch

import textwrap



color_discrete_map_presence=pd.Series({'Started':'#0068c9',
                                 'Sub in':'#83c9ff',
                                 'Not played':'#ff2b2b',
                                 })

color_discrete_map_bool = {True:'#018749', False:'rgba(125,125,125,0.5)'}


color_maps = {
    'presence':color_discrete_map_presence,
    'bool':color_discrete_map_bool
}

TOOLTIP_SIZE = 25
DAY_IN_MS = 1000 * 3600 * 24


def get_mpl_pitch():
    return Pitch(pitch_type='statsbomb', line_zorder=2,
              pitch_color='white', line_color='gray', )


def plot_pitch(field_dimen=(120, 80), 
               background="#dfe3eb", 
               color_lines="white", 
               width=800, height=600,
               xlimits=None,
               ylimits=None,
               y_inverted=False,
               offensive_half=False):
    """
    Plots a football pitch with specified dimensions and markings.

    Args:
    - field_dimen (tuple, optional): Dimensions of the field in meters (length, width). Defaults to (120, 80).
    - background (str, optional): Background color of the plot. Defaults to "#dfe3eb".
    - color_lines (str, optional): Color of the pitch lines. Defaults to "white".
    - width (int, optional): Width of the plot in pixels. Defaults to 800.
    - height (int, optional): Height of the plot in pixels. Defaults to 600.
    - xlimits (tuple, optional): Limits of the x-axis. Defaults to None.
    - ylimits (tuple, optional): Limits of the y-axis. Defaults to None.
    - y_inverted (bool, optional): Whether to invert the y-axis (useful for some plotting libraries). Defaults to False.
    - offensive_half (bool, optional): Whether to show only the offensive half of the pitch. Defaults to False.

    Returns:
    go.Figure: Plotly figure object representing the football pitch.
    tuple: Tuple of field dimensions (length, width).
    """
    field_length = field_dimen[0]
    field_width = field_dimen[1]

    fig = go.Figure()

    padding = 3

    # Set x-axis range based on provided or default limits
    if xlimits:
        xrange = [-padding + xlimits[0], xlimits[1] + padding]
    else:
        xrange = [-padding, field_length + padding]

    # Set y-axis range based on provided or default limits
    if ylimits:
        yrange = [-padding + ylimits[0], ylimits[1] + padding]
    else:
        yrange = [-padding, field_width + padding]

    # Update layout of the figure
    fig.update_layout(
        plot_bgcolor=background,
        width=width / 2 if offensive_half else width,
        height=height,
        xaxis=dict(range=xrange, showgrid=False, zeroline=False),
        yaxis=dict(range=yrange, showgrid=False, zeroline=False)
    )

    # Add pitch boundaries
    fig.add_shape(type="rect", x0=0, y0=0, x1=field_length, y1=field_width,
                  line=dict(color=color_lines, width=3), layer="below")

    # Add halfway line
    fig.add_shape(type="line", x0=field_length / 2, y0=0, x1=field_length / 2, y1=field_width,
                  line=dict(color=color_lines, width=3), layer="below")

    # Add center circle
    fig.add_shape(type="circle", x0=field_length / 2 - 10, y0=field_width / 2 - 10,
                  x1=field_length / 2 + 10, y1=field_width / 2 + 10,
                  line=dict(color=color_lines, width=3), layer="below")

    # Add penalty areas
    fig.add_shape(type="rect", x0=0, y0=field_width / 2 - 22, x1=18, y1=field_width / 2 + 22,
                  line=dict(color=color_lines, width=3), layer="below")
    fig.add_shape(type="rect", x0=field_length - 18, y0=field_width / 2 - 22, x1=field_length, y1=field_width / 2 + 22,
                  line=dict(color=color_lines, width=3), layer="below")

    # Add goal areas
    fig.add_shape(type="rect", x0=0, y0=field_width / 2 - 7.32, x1=6, y1=field_width / 2 + 7.32,
                  line=dict(color=color_lines, width=3), layer="below")
    fig.add_shape(type="rect", x0=field_length - 6, y0=field_width / 2 - 7.32, x1=field_length, y1=field_width / 2 + 7.32,
                  line=dict(color=color_lines, width=3), layer="below")

    # Add penalty spots
    fig.add_shape(type="circle", x0=12 - 0.8, y0=field_width / 2 - 0.8, x1=12 + 0.8, y1=field_width / 2 + 0.8,
                  line=dict(color=color_lines, width=3), layer="below")
    fig.add_shape(type="circle", x0=field_length - 12 - 0.8, y0=field_width / 2 - 0.8, x1=field_length - 12 + 0.8, y1=field_width / 2 + 0.8,
                  line=dict(color=color_lines, width=3), layer="below")

    # Update layout for y-axis inversion if needed
    if y_inverted:
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
        )

    return fig, field_dimen




def plot_football_field_with_positions(player_positions=None, width=800, height=600):
    fig, field_dimen = plot_pitch(background="green")

    # Define positions and their coordinates on the field (adjust as needed)
    positions_loc = {
        1: (10, 40),
        2: (30, 10),
        3: (30, 25),
        4: (30, 40),
        5: (30, 55),
        6: (30, 70),
        7: (50, 10),
        8: (50, 70),
        9: (50, 25),
        10: (50, 40),
        11: (50, 55),
        12: (70, 10),
        13: (70, 25),
        14: (70, 40),
        15: (70, 55),
        16: (70, 70),
        17: (90, 10),
        18: (90, 25),
        19: (90, 40),
        20: (90, 55),
        21: (90, 70),
        22: (110, 25),
        23: (110, 40),
        24: (110, 55),
        25: (100, 40),
    }

    # Calculate total minutes played
    total_min = player_positions['minutes_on_field'].sum()

    # Iterate over each player's position record
    for i, pos_record in player_positions.iterrows():
        # Retrieve coordinates for the position
        x, y = positions_loc[position_dict[pos_record['position_name']]]
        
        # Calculate marker size based on proportion of minutes played
        marker_size = (pos_record['minutes_on_field'] / total_min) * 30

        # Ensure a minimum marker size for visibility
        if marker_size < 10:
            marker_size = 10

        # Add trace for each player position
        fig.add_trace(go.Scatter(
            x=[x], y=[y], mode='markers',
            marker=dict(size=marker_size, color='black'),
            text=[pos_record['position_name']],
            textposition="top center",
            textfont=dict(color="white", size=12),
            hoverinfo='text',
            hovertext=f"<b>Position:</b> {pos_record['position_name']} <br>"
                      f"<b>Minutes played:</b> {pos_record['minutes_on_field']} "
                      f"({round(pos_record['minutes_on_field'] / total_min * 100)}%)"
        ))

    # Update figure layout
    fig.update_layout(
        title=f"Minutes on field distribution by role <br><sup style='color: gray'>Total minutes played: {total_min}</sup>",
        title_font_size=16,
        width=width,
        height=height,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        showlegend=False,
        hoverlabel=dict(font_size=12),
    )

    return fig



def create_donut_chart(labels, values, title='', 
                       type=None, annotation="", 
                       width=800, height=600, 
                       resize_by='width',
                       title_x=0.5, title_y=0.9):

    """
    Create a donut chart using Plotly.

    Parameters:
        labels (list): List of labels for each segment of the donut chart.
        values (list): List of values corresponding to each segment of the donut chart.
        title (str): Title of the donut chart.
        type (str): Type of color map (optional).
        annotation (str): Annotation text to display in the center of the donut chart (default: "").
        width (int): Width of the plot (default: 800).
        height (int): Height of the plot (default: 600).
        resize_by (str): Dimension to resize by ('width' or 'height', default: 'width').
        title_x (float): Horizontal position of the title (default: 0.5).
        title_y (float): Vertical position of the title (default: 0.9).

    Returns:
        fig (plotly.graph_objs.Figure): Plotly figure object containing the donut chart.
    """
    # Validate resize_by parameter
    if resize_by not in ['width', 'height']:
        raise ValueError("Parameter 'resize_by' must be either 'width' or 'height'.")

    # Calculate resize factor based on width or height
    resize_factor = width if resize_by == 'width' else height

    # Define color map based on type (if provided)
    cmap = color_maps[type] if type and type in color_maps else None

    # Create Plotly figure for donut chart
    fig = go.Figure(data=[
        go.Pie(labels=labels, values=values, hole=0.5,
               hoverinfo='skip',
               marker=dict(colors=cmap),
               textfont=dict(size=resize_factor * 0.025),
               texttemplate='%{label}<br>%{value} (%{percent})'
               )
    ])

    # Update layout of the figure
    fig.update_layout(
        title=title,
        title_x=title_x,
        title_y=title_y,
        title_font=dict(size=0.037 * resize_factor),  # Title font size scaled by resize factor
        showlegend=False,
        margin=dict(autoexpand=True),
        width=width,
        height=height,
        annotations=[
            dict(
                text=f"Total<br>{sum(values)}" if annotation == "" else annotation,
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=0.03 * resize_factor),
            )
        ]
    )

    return fig


def create_radar_chart(traces, labels, title='', fill=False, 
                       width=800, height=600, 
                       showlegend = False, label_bold = False, label_font_size=16):

    """
    Create a radar chart using Plotly.

    Parameters:
    - traces (dict): Dictionary of traces to plot on the radar chart. Each key is the trace name,
                     and each value is a dictionary containing 'percentiles', 'real_values', 'color'
                     (optional) to define the data for the trace.
    - labels (list): List of labels for each axis of the radar chart.
    - title (str): Title of the radar chart.
    - fill (bool): Whether to fill the area inside the radar lines (default: False).
    - width (int): Width of the plot in pixels (default: 800).
    - height (int): Height of the plot in pixels (default: 600).
    - showlegend (bool): Whether to show the legend (default: False).
    - label_bold (bool): Whether to display labels in bold (default: False).
    - label_font_size (int): Font size for labels (default: 16).

    Returns:
    - fig (plotly.graph_objs.Figure): Plotly figure object containing the radar chart.
    """
        
    # Wrap labels and apply formatting
    radar_labels = []
    for label in labels:
        wrapped_label = textwrap.fill(label, 15).replace('\n','<br>')
        if label_bold:
            wrapped_label = f"<span style='font-size:{label_font_size};'><b>{wrapped_label}</b></span>"
        else:
            wrapped_label = f"<span style='font-size:{label_font_size};'>{wrapped_label}</span>"
        radar_labels.append(wrapped_label)

    # Initialize Plotly figure
    fig = go.Figure()
    
    # Add the first label at the end to close the loop
    radar_labels = radar_labels+[radar_labels[0]]

    # Iterate through traces and add them to the radar chart
    for trace_name, trace in traces.items():
        
        # Extend percentiles and real_values to close the loop
        percentiles = trace['percentiles']+[trace['percentiles'][0]-0000000.1]
        real_values = trace['real_values']+[trace['real_values'][0]]
        color = trace['color'] if 'color' in trace else None

        # Define hovertemplate based on showlegend option
        if showlegend:
            hovertemplate = [f"<b>{label}<b>: {round(real_value, 2)}" \
                             for label, percentile, real_value in zip(labels, percentiles, real_values)]
        else:
            hovertemplate = [f"{trace_name}<br><b>{label}<b>: {round(real_value, 2)}" \
                             for label, percentile, real_value in zip(labels, percentiles, real_values)]

        # Add Scatterpolar trace to the figure
        fig.add_trace(go.Scatterpolar(
            r=percentiles,
            theta=radar_labels,
            hoverinfo='text',
            hovertemplate=hovertemplate,
            name=trace_name if showlegend else '',
            marker=dict(color=color),
            textfont=dict(size=30, color='black')
        ))

        

    # Update layout of the figure
    fig.update_layout(
        title=title,
        title_x = 0.40,
        title_font=dict(color="black", size=30),  # Default font color,
        showlegend=False,
        width=width,
        height=height,
        hoverlabel=dict(font_size=TOOLTIP_SIZE),
        hovermode="x unified",
        polar = dict(
            radialaxis=dict(
                visible = False,
                range = [0, 100]
            )
        )
    )

    # Update layout to show legend if showlegend is True
    if showlegend:
        fig.update_layout(
            showlegend=showlegend,
            legend=dict(
                title='Players',
                font=dict(size=10),
                itemsizing='constant',
                y=1.5,
                yanchor="top",
                x=0.5,
                xanchor='center',
                orientation="h"
            )
        )

    return fig


def create_pizza_plot(labels, percentiles, title, subtitle):
    """
    Create a pizza plot (radar chart-like) using PyPizza library.

    Parameters:
    - labels (list): List of parameter labels for the pizza plot.
    - percentiles (list): List of percentile values corresponding to each parameter.
    - title (str): Title of the pizza plot.
    - subtitle (str): Subtitle or description for the pizza plot.

    Returns:
    - fig (matplotlib.figure.Figure): Matplotlib figure object containing the pizza plot.
    """
    # Generate colors for slices based on percentiles
    colormap = cm.RdYlGn
    slice_colors = [colormap(p/100) for p in percentiles]

    # Text colors for parameter labels and values
    text_colors = ['black']*len(percentiles)

    # Format labels for display on the plot, replacing underscores with spaces and wrapping text
    labels = [textwrap.fill(label.replace('_', ' '), 10) for label in labels]

    # Instantiate PyPizza class
    baker = PyPizza(
        params=labels,                  # List of parameters
        straight_line_color="#000000",  # Color for straight lines
        straight_line_lw=1,             # Linewidth for straight lines
        last_circle_lw=1,               # Linewidth of last circle
        other_circle_lw=0,              # Linewidth for other circles
        other_circle_ls="-.",           # Linestyle for other circles
        background_color='white',       # Background color
    )

    # Plot the pizza
    fig, ax = baker.make_pizza(
        percentiles,              # List of values (percentiles)
        figsize=(7, 7),           # Adjust figsize according to your need
        param_location=115,       # Position where the parameters will be added
        slice_colors=slice_colors,      # Color for individual slices
        value_colors=text_colors,        # Color for parameter values
        value_bck_colors=slice_colors,  # Background color for parameter values
        kwargs_params=dict(
            color="#000000", fontsize=10, va="center"
        ),                   # Keyword arguments for parameters
        kwargs_values=dict(
            color="#000000", fontsize=10, zorder=3,
            bbox=dict(
                edgecolor="#000000", facecolor="cornflowerblue",
                boxstyle="round,pad=0.2", lw=1
            )
        )                    # Keyword arguments for parameter values
    )

    # Customize plot title and subtitle
    fig.suptitle(title, fontsize=16, fontweight='bold')
    ax.set_title(subtitle, fontsize=12)

    return fig



def create_linear_plot(metrics, players_stat_df, percentiles_player, rankings_player, index_column='player_name'):
    """
    Create a linear plot (scatter plot) comparing player statistics across multiple metrics.

    Parameters:
    - metrics (list): List of dictionaries where each dictionary contains 'name' (metric name), 
                      'visible_name' (display name), and 'lower_is_better' (boolean).
    - players_stat_df (pandas.DataFrame): DataFrame containing player statistics with player names as index.
    - percentiles_player (dict): Dictionary containing percentiles for each metric for a specific player.
    - rankings_player (dict): Dictionary containing rankings for each metric for a specific player.
    - index_column (str): Column name to set as index in players_stat_df (default is 'player_name').

    Returns:
    - fig (plotly.graph_objs.Figure): Plotly figure object containing the linear plot.
    """
    # Set DataFrame index
    df = players_stat_df.set_index(index_column)

    # Initialize Plotly figure
    fig = go.Figure()
    
    # Iterate over metrics to create scatter plots
    for idx, metric in enumerate(metrics):
        # Calculate percentiles for the current metric
        percentiles = df[metric['name']].rank(method='dense', ascending=not metric['lower_is_better'], pct=True) * 100
        
        # Add trace for current metric's percentiles
        fig.add_trace(
            go.Scatter(
                y=[metric['visible_name']] * len(percentiles),
                x=percentiles,
                mode='markers',
                name=metric['visible_name'],
                marker=dict(
                    color='rgba(0, 100, 200, 0.2)',
                    size=10
                ),
                showlegend=False
            )
        )

        # Highlight the specified player's ranking for the current metric
        fig.add_trace(
            go.Scatter(
                x=[percentiles_player[metric['name']]],
                y=[metric['visible_name']],
                mode='markers',
                marker=dict(
                    color='rgba(255, 0, 0, 1)',
                    size=15,
                    line=dict(
                        color='DarkSlateGrey',
                        width=2
                    )
                ),
                name='Player',
                showlegend=False
            )
        )

        # Add median percentile marker for the current metric
        fig.add_trace(
            go.Scatter(
                x=[percentiles.median()],
                y=[metric['visible_name']],
                mode='markers',
                marker=dict(
                    color='rgba(0, 255, 0, 1)',
                    size=15,
                    line=dict(
                        color='DarkSlateGrey',
                        width=2
                    )
                ),
                name='Median',
                showlegend=False
            )
        )

    # Update layout
    fig.update_layout(
        title='Player Statistics Comparison',
        xaxis_title='Percentile',
        yaxis_title='Metric',
        width=1200,
        height=800,
        margin=dict(l=200, r=200, t=100, b=100),  # Adjust margins as needed
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        hoverlabel=dict(
            font_size=16
        )
    )

    return fig




def create_shot_map(shots_events, width=1200, height=800):
    """
    Create a shot map using Plotly Express scatter plot.

    Parameters:
    - shots_events (pandas.DataFrame): DataFrame containing shot events data.
    - width (int): Width of the plot (default is 1200).
    - height (int): Height of the plot (default is 800).

    Returns:
    - fig (plotly.graph_objs.Figure): Plotly figure object containing the shot map.
    """
    # Determine plot limits based on shot events data
    xlimits = (shots_events.start_x.min() - 5, 120)
    ylimits = (min(shots_events.start_y.min() - 5, 0), max(shots_events.start_y.max() + 5, 80))

    # Plot the football pitch using custom function plot_pitch
    fig, _ = plot_pitch(y_inverted=True, offensive_half=True, xlimits=xlimits, ylimits=ylimits, width=width, height=height, background='green')

    # Define color and symbol mappings based on shot outcome
    outcomes = list(shots_events['shot_outcome_name'].unique())
    if 'Goal' in outcomes:
        outcomes.remove('Goal')
        outcomes = ['Goal'] + outcomes

    color_map = {t: 'blue' if t == 'Goal' else 'red' for t in outcomes}
    symbol_map = {
        'Goal': 'circle',
        'Blocked': 'square',
        'Saved': 'diamond',
        'Post': 'cross',
        'Off T': 'x',
        'Wayward': 'triangle-up',
        'Saved to Post': 'triangle-down'
    }

    # Create the scatter plot using Plotly Express
    scatter_fig = px.scatter(
        shots_events,
        x='start_x',
        y='start_y',
        color='shot_outcome_name',
        size='shot_statsbomb_xg',
        symbol='shot_outcome_name',
        hover_data={
            'minute': True,
            'shot_statsbomb_xg': ':.2f',
            'shot_body_part_name': True,
            'shot_type_name': True,
        },
        labels={
            'shot_outcome_name': 'Shot Outcome',
            'shot_statsbomb_xg': 'xG',
            'shot_body_part_name': 'Body part',
            'shot_type_name': 'Situation'
        },
        title='',
        opacity=0.5,
        category_orders={'shot_outcome_name': outcomes},
        color_discrete_map=color_map,
        symbol_map=symbol_map
    )

    # Add the scatter plot traces to the football pitch figure
    for trace in scatter_fig.data:
        fig.add_trace(trace)

    # Update layout to show legend and customize hover label font size
    fig.update_layout(
        showlegend=True,
        hoverlabel=dict(font_size=10),
        legend=dict(
            title='Shot Outcome',
            font=dict(size=15),
            itemsizing='constant',
            y=1.2,
            yanchor="top",
            x=0.5,
            xanchor='center',
            orientation="h"
        )
    )

    return fig


def create_heat_map(df, x_column, y_column, 
                    statistic='count', bins=(6, 5), normalize=True,  
                    cmap='Reds',
                    title='',
                    endnote='',
                    single_event_detail=False,
                    axs=None):
    
    """
    Generates a heatmap plot on a football pitch using Matplotlib and mplsoccer.

    Parameters:
        df (pd.DataFrame): DataFrame containing the data to plot.
        x_column (str): Column name in `df` to use for the x-axis coordinates.
        y_column (str): Column name in `df` to use for the y-axis coordinates.
        statistic (str, optional): Type of statistic to compute for the heatmap (default is 'count').
        bins (tuple, optional): Number of bins for heatmap grid in (x, y) format (default is (6, 5)).
        normalize (bool, optional): If True, normalizes the heatmap values (default is True).
        cmap (str, optional): Colormap for the heatmap (default is 'Reds').
        title (str, optional): Title of the plot (default is '').
        endnote (str, optional): Endnote text (default is '').
        single_event_detail (bool, optional): If True, plots individual events as points on the heatmap (default is False).
        axs (dict, optional): Optional pre-defined axes grid for the pitch (if None, a new pitch grid is created).

    Returns:
        fig (matplotlib.figure.Figure): Matplotlib Figure object containing the heatmap plot.
    """

    # Initialize the pitch using mplsoccer's Pitch class
    if axs is None:
        pitch = get_mpl_pitch()  # Assuming get_mpl_pitch() returns a mplsoccer Pitch instance
        
        # Create the figure and axes grid for the pitch
        fig, axs = pitch.grid(endnote_height=0.03, endnote_space=0,
                              grid_width=0.88, left=0.025,
                              title_height=0.06, title_space=0,
                              axis=False,
                              grid_height=0.86)
    
    # Define path effects for labels
    path_eff = [path_effects.Stroke(linewidth=1.5, foreground='black'),
                path_effects.Normal()]
    
    # Compute the heatmap statistics using mplsoccer's bin_statistic method
    bin_statistic = pitch.bin_statistic(df[x_column], df[y_column], statistic=statistic, bins=bins, normalize=normalize)
    
    # Plot the heatmap on the pitch axes
    pcm = pitch.heatmap(bin_statistic, ax=axs['pitch'], cmap=cmap, edgecolor='#f9f9f9')
    
    # Add labels to the heatmap cells
    labels = pitch.label_heatmap(bin_statistic, color='white', fontsize=25,
                                 ax=axs['pitch'], ha='center', va='center',
                                 str_format='{:.0%}', path_effects=path_eff)
    
    # Optionally plot individual events as points on the heatmap
    if single_event_detail:
        axs['pitch'].scatter(df[x_column], df[y_column], alpha=0.05, color='black')

    # Add title to the title axes
    ax_title = axs['title'].text(0.5, 0.5, title, color='black',
                                 va='center', ha='center', fontsize=30)
    
    # Add endnote to the endnote axes
    axs['endnote'].text(1, 0.5, endnote, va='center', ha='right', fontsize=15,
                        color='gray')

    return fig


def create_bar_chart(labels, 
                     values, 
                     width=500, height=500, 
                     orientation='h', 
                     title='', 
                     resize_by='width', 
                     y_inverted=False,
                     wrap_label = True,
                     label_font_size=None,
                     label_bold=True,
                     color=None,
                     fig=None,
                     bar_width=None,
                     barmode=None,
                     text = '',
                     trace_name = ''):
    """
    Creates a horizontal or vertical bar chart using Plotly.

    Parameters:
        labels (list): List of labels for each bar in the chart.
        values (list): List of values corresponding to each bar.
        width (int, optional): Width of the plot (default is 500).
        height (int, optional): Height of the plot (default is 500).
        orientation (str, optional): Orientation of the bars ('h' for horizontal, 'v' for vertical, default is 'h').
        title (str, optional): Title of the chart (default is '').
        resize_by (str, optional): Determines whether to resize by 'width' or 'height' (default is 'width').
        y_inverted (bool, optional): If True, inverts the y-axis (default is False).
        label_font_size (str, optional): Font size of the labels (default is None).
        label_bold (bool, optional): If True, makes the labels bold (default is True).
        color (str or list, optional): Color(s) for the bars (default is None).
        fig (plotly.graph_objs.Figure, optional): Plotly Figure object to which the bars will be added (default is None).
        bar_width (float, optional): Width of the bars (default is None).
        barmode (str, optional): Mode for bar positioning ('stack', 'group', 'overlay', 'relative', default is None).

    Returns:
        fig (plotly.graph_objs.Figure): Plotly Figure object containing the bar chart.
    """
    
    if resize_by == 'width':
        resize_by = width
    elif resize_by == 'height':
        resize_by = height

    if wrap_label:
        chart_labels = []
        for label in labels:
            wrapped_label = textwrap.fill(label, 15).replace('\n', '<br>')
            if label_bold:
                wrapped_label = f"<span style='font-size:{label_font_size};'><b>{wrapped_label}</b></span>"
            else:
                wrapped_label = f"<span style='font-size:{label_font_size};'>{wrapped_label}</span>"
            chart_labels.append(wrapped_label)
    else:
        chart_labels = labels
    

    if orientation == 'h':
        x_data = values
        y_data = chart_labels
    else:
        x_data = chart_labels
        y_data = values

    if not fig:
        fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        orientation=orientation,
        marker=dict(color=color),
        text = text,
        name=trace_name,
        hovertemplate='%{label}: %{value}',
        width=bar_width
    ))
    

    fig.update_layout(
        title=title,
        title_x=0.35,
        title_y=0.9,
        title_font=dict(size=0.037 * resize_by),
        width=width,
        height=height,
        barmode=barmode
    )

    if y_inverted:
        if orientation == 'h':
            fig.update_layout(yaxis=dict(autorange="reversed"))
        else:
            fig.update_layout(xaxis=dict(autorange="reversed"))

    return fig
    


def create_scatter_plot(df, x_dict, y_dict, width=500, height=500, 
                        color_column = None,
                        color_map_type = None):
    
    """
    Creates a scatter plot using Plotly based on the provided DataFrame and dictionaries for x and y axes.

    Parameters:
        df (pandas.DataFrame): DataFrame containing the data to be plotted.
        x_dict (dict): Dictionary with keys 'name' and 'visible_name' specifying the column name and visible label for the x-axis.
        y_dict (dict): Dictionary with keys 'name' and 'visible_name' specifying the column name and visible label for the y-axis.
        width (int, optional): Width of the plot (default is 500).
        height (int, optional): Height of the plot (default is 500).
        color_column (str, optional): Column name in the DataFrame to use for color coding points (default is None).
        color_map_type (str, optional): Type of color map to use for coloring points (default is None).

    Returns:
        fig (plotly.graph_objs.Figure): Plotly Figure object containing the scatter plot.
    """


    fig = px.scatter(
        df,
        x=x_dict['name'],
        y=y_dict['name'],
        color = color_column,
        hover_name='player_name',
        hover_data={
            color_column:False
        },
        labels={
            x_dict['name']: x_dict['visible_name'],
            y_dict['name']: y_dict['visible_name'],
        },
        title='',
        opacity=0.5,
        color_discrete_map = color_maps[color_map_type] if color_map_type else None,
    )

    fig.update_layout(
        width=500, 
        height=500,
        showlegend = False
        
    )

    fig.update_traces(marker=dict(size=10))

    return fig
         
        

   

        

