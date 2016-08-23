"""
inputs.py

    input functions for Wind Power component
"""
import os.path
from pandas import read_csv
from yaml import load
from config import UNKNOWN

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    Loads wind_power_data.csv
    
    pre:
        wind_power_data.csv exists at data_dir
    post:
        the values in wind_power_data.csv are returned as a dictionary 
    """
    data_file = os.path.join(data_dir, "wind_power_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    
def load_wind_costs_table (data_dir):
    """
    loads the wind cost table
    
    pre:
        wind_costs.csv exists at data_dir
    post:
        the wind cost values are returned as a pandas DataFrame
    """
    data_file = os.path.join(data_dir, "wind_costs.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data.index =data.index.astype(str)
    return data
    
def load_project_details (data_dir):
    """
    load details related to exitign projects
    
    pre:
        data_dir is a directory with  'project_development_timeframes.csv',
        and "wind_projects.yaml" in it 
    
    post:
        retunrns a dictonary wht the keys 'phase'(str), 
        'proposed capacity'(float), 'proposed generation'(float),
        'distance to resource'(float), 'generation capital cost'(float),
        'transmission capital cost'(float), 'operational costs'(float),
        'expected years to operation'(int),
    """
    try:
        tag = os.path.split(data_dir)[1].split('+')
        project_type = tag[1]
        tag = tag[1] + '+' +tag[2]
        if project_type != 'wind':
            tag = None
    except IndexError:
        tag = None
    
    # get the estimated years to operation
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#', index_col=0, header=0)['Wind']

    if tag is None:
        # if no data make some
        yto = int(round(float(data['Reconnaissance'])))
        return {'phase': 'Reconnaissance',
                'proposed capacity': UNKNOWN,
                'proposed generation': UNKNOWN,
                'distance to resource': UNKNOWN,
                'generation capital cost': UNKNOWN,
                'transmission capital cost': UNKNOWN,
                'operational costs': UNKNOWN,
                'expected years to operation': yto,
                }
                
    #read data
    with open(os.path.join(data_dir, "wind_projects.yaml"), 'r') as fd:
        dets = load(fd)[tag]
      
    # correct number years if nessary
    if dets['expected years to operation'] == UNKNOWN:
        if dets['phase'] == 'Operational':
            yto = 0
        else:
            try:
                yto = int(round(float(data[dets['phase']])))
            except TypeError:
                yto =0
        #~ print yto
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = \
        int(dets['expected years to operation'])    
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'resource data':process_data_import,
                   'costs':load_wind_costs_table,
                   'project details': load_project_details,
                   }
