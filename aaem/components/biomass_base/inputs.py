"""
Biomass Base inputs
-------------------

    input functions for Biomass Base component
    
"""
import os.path
from pandas import read_csv

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """read the data from biomass_data.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns 
    -------
    data : dict
        keys are 'peak month % of total', 'capacity factor', 'Distance', 
        and sufficient biomass
    
    """
    data_file = os.path.join(data_dir, "biomass_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data = data['value'].to_dict()
    data['peak month % of total'] = float(data['peak month % of total'])
    data['capacity factor'] = float(data['capacity factor'])
    data['Distance'] = float(data['Distance to Heating Reference Community'])
    
    key = 'sufficient biomass'
    try:
        sufficient = data[key].lower() == "yes"
    except AttributeError:
        sufficient = False
    data[key] = sufficient
    return data

## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data':process_data_import,}
