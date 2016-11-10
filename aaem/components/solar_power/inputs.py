"""
inputs.py

    input functions for Solar Power component
"""
import os.path
from pandas import read_csv

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "solar_power_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data = data['value'].to_dict()
    data['Output per 10kW Solar PV'] = float(data['Output per 10kW Solar PV'])
    return data

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data':process_data_import,}
    
