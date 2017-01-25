"""
inputs.py

    input functions for Non-Residential Building Efficiency component
"""
import os.path
from pandas import read_csv

def load_building_data (data_dir):
    """ Function doc """
    data_file = os.path.join(data_dir, "community_buildings.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return data
    
def load_num_buildings (data_dir):
    """ Function doc """
    data_file = os.path.join(data_dir, "non-res_count.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return int(data.ix["Buildings"])

def load_building_estimates (data_dir):
    """ Function doc """
    data_file = os.path.join(data_dir, "non-res_consumption_estimates.csv")
    
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    
    return data
    
            
yaml_import_lib = {'com building data': load_building_data,
                   'number buildings': load_num_buildings,
                   'com building estimates': load_building_estimates}
