"""
inputs.py

    input functions for Residential Building Efficiency component
"""
import os.path
import numpy as np
from pandas import read_csv

def process_data_import(data_dir):
    """
    """
    data_file = os.path.join(data_dir, "residential_data.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    data.ix["Notes"]['value'] = np.nan
    if data.ix["average kWh per house"]['value'] == "CALC_FOR_INTERTIE":
        data.ix["average kWh per house"]['value'] = np.nan
    data['value'] = data['value'].astype(float) 
    
    
    return data
        
yaml_import_lib = {'data': process_data_import}
