"""
Wind Power Inputs
-----------------

input functions for Wind Power component
    
"""
import os.path
from pandas import read_csv
from yaml import load
from config import UNKNOWN

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """Load data from wind_power_data.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    dict
        wind data
    """
    data_file = os.path.join(data_dir, "wind_power_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    
def load_wind_costs_table (data_dir):
    """Loads the wind cost table.
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    dict
        wind cost data
    """
    data_file = os.path.join(data_dir, "wind_kw_costs.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    data.index =data.index.astype(str)
    #~ print data
    return data
    
def load_project_details (data_dir):
    """Load details related to exitign projects.
    
    Parameters
    ----------
    data_dir : path
        is a directory with  'project_development_timeframes.csv',
        and "project_name_projects.yaml" in it 
    
    Returns
    -------
    dict
        has the keys 'phase'(str), 'proposed capacity'(float),
        'proposed generation'(float),'distance to resource'(float), 
        'generation capital cost'(float), 'transmission capital cost'(float), 
        'operational costs'(float), 'expected years to operation'(int),
    """
    tag = os.path.split(data_dir)[1].split('+')
    data_dir = os.path.join(os.path.split(data_dir)[0],tag[0])
    try:
        project_type = tag[1]
        if project_type != 'wind':
            tag = None
        else:
            tag = '+'.join(tag[1:])
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
