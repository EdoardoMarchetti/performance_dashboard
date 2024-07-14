from datetime import datetime, timedelta

import numpy as np
import pandas as pd

def convert_to_seconds(time_str):
    """
    Convert a time string in the format '%H:%M:%S' to the total number of seconds.
    """
    time_obj = datetime.strptime(time_str, '%H:%M:%S')
    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    return total_seconds

# Apply the function to each value in the pandas Series
def convert_series_to_seconds(time_series):
    return time_series.apply(convert_to_seconds)


def sort_vel_intervals(vel_intervals):
    # Define a custom sorting key based on the lower bound of each interval
    def get_lower_bound(interval):
        # Split the interval string and extract the lower bound
        return int(interval.split('-')[0].strip('>').strip('< ').split()[0])

    # Sort vel_intervals based on the lower bound using the custom key
    sorted_intervals = sorted(vel_intervals, key=get_lower_bound)

    return sorted_intervals


def filter_velocities(vel_intervals, velocities_distance, velocities_temp):
    filtered_distance = []
    filtered_temp = []

    for interval in vel_intervals:
        for vel_dist, vel_temp in zip(velocities_distance, velocities_temp):
            if interval.replace(' ','') in vel_dist.replace(' ',''):
                filtered_distance.append(vel_dist)
            if interval in vel_temp:
                filtered_temp.append(vel_temp)

    return filtered_distance, filtered_temp


def ensure_list(value):
    """
    Ensure the input is a list. If the input is a pd.Series, convert it to a list.
    If the input is a single value, wrap it in a list.
    """
    if isinstance(value, pd.Series) or isinstance(value, pd.Series):
        return value.tolist()
    return [value]

def ensure_array(value):
    """
    Ensure the input is a numpy array. If the input is a pd.Series, convert it to a numpy array.
    If the input is a single value, wrap it in a numpy array.
    """
    if isinstance(value, pd.Series) or isinstance(value, pd.Series):
        return value.to_numpy()
    return np.array([value])


# Function to convert time string to total seconds
def convert_to_seconds(time_str):
    time_obj = datetime.strptime(time_str, '%H:%M:%S')
    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    return total_seconds

# Function to convert total seconds back to time string
def convert_to_time_string(total_seconds):
    return str(timedelta(seconds=total_seconds))

def sum_time_columns(df):
    if isinstance(df, pd.Series) == 1:
        #df_seconds = df.applymap(convert_to_seconds)
        sum_seconds = convert_to_seconds(df.iloc)  # Directly take the first row if it's a single row
    else:
        df_seconds = df.applymap(convert_to_seconds)
        sum_seconds = df_seconds.sum()

    
    return sum_seconds


def convert_comma_float(value):
    """
    Convert a string representing a float with commas as decimal separators to a float.

    Args:
    - value (str): String representing a float with commas as decimal separators.

    Returns:
    - float: The converted float value.
    """
    if isinstance(value, str):
        # Replace the comma with a dot
        value = value.replace(',', '.')
        
    # Convert the string to a float
    return float(value)