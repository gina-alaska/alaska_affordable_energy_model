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
        data as a Pandas.Dataframe
    
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
        a dictionary of 'Tempeature', 'COP', and 'PPercent of Total Capacity
    
    """
    data = read_csv(os.path.join(data_dir,'ashp_perfromance_data.csv'))
    rv = {}
    rv['Temperature'] = data['Temperature'].tolist()
    rv['COP'] = data['COP'].tolist()
    rv['Percent of Total Capacity'] = data['Percent of Total Capacity'].tolist()
    return rv
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'perfromance data':import_perfromance_data,
                    'data':process_data_import}
