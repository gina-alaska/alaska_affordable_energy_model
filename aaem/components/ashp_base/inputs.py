"""
inputs.py

    input functions for Air Source Heat Pumps Base component
"""
import os.path
from pandas import read_csv

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    data = read_csv(os.path.join(data_dir,'ashp_climate_data.csv'),index_col=0,comment = '#')
    return  data
    
def import_perfromance_data (data_dir):
    """ Function doc """
    data = read_csv(os.path.join(data_dir,'ashp_perfromance_data.csv'))
    rv = {}
    rv['Temperature'] = data['Temperature'].tolist()
    rv['COP'] = data['COP'].tolist()
    rv['Percent of Total Capacity'] = data['Percent of Total Capacity'].tolist()
    return rv
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'perfromance data':import_perfromance_data,
                    'data':process_data_import}
