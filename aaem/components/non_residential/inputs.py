"""
Non-Residential Efficiency inputs
---------------------------------

input functions for Non-Residential Efficiency component
    
"""
import os.path
from pandas import read_csv

def load_building_data (data_dir):
    """Load building inventory data from community_buildings.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    DataFrame
        data from inventory
    """
    data_file = os.path.join(data_dir, "community_buildings.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return data
    
def load_num_buildings (data_dir):
    """load estimated # of buildings in community
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    int
        number of buildings
        
    """
    data_file = os.path.join(data_dir, "non-res_count.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return int(data.ix["Buildings"])

def load_building_estimates (data_dir):
    """load consumption estimates
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    DataFrame
        estimate data 
    """
    data_file = os.path.join(data_dir, "non-res_consumption_estimates.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return data
    
            
yaml_import_lib = {'com building data': load_building_data,
                   'number buildings': load_num_buildings,
                   'com building estimates': load_building_estimates}
