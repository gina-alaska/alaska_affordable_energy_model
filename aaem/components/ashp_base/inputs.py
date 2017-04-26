"""
Air Source Heat Pump Base inputs
--------------------------------

    input functions for Air Source Heat Pump Base component
    
"""
import os.path
from pandas import read_csv

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """read the data from ashp_climate_data.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns 
    -------
    data : DataFrame
        cliamte data from component to use
    
    """
    data = read_csv(os.path.join(data_dir,'ashp_climate_data.csv'),
        index_col=0,comment = '#')
    return  data
    
def import_perfromance_data (data_dir):
    """read the data from ashp_perfromance_data.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns 
    -------
    data : dict
         with 'Tempeature', 'COP', and 'PPercent of Total Capacity
    
    """
    in_data = read_csv(os.path.join(data_dir,'ashp_perfromance_data.csv'))
    data = {}
    data['Temperature'] = in_data['Temperature'].tolist()
    data['COP'] = in_data['COP'].tolist()
    data['Percent of Total Capacity'] = in_data['Percent of Total Capacity'].tolist()
    return data
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'perfromance data':import_perfromance_data,
                    'data':process_data_import}
