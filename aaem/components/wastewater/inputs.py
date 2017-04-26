"""
Water Wastewater Inputs
-----------------------

input functions for Water Wastewater component
    
"""
import os.path
from pandas import read_csv

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """Load data from wastewater_data.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    dict
        transmission data
    """
    data_file = os.path.join(data_dir, "wastewater_data.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)    
    
    return data

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data': process_data_import}
