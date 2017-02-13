"""
Transmission Inputs
-------------------

input functions for Transmission component
    
"""
import os.path
from pandas import read_csv
from yaml import load
from config import UNKNOWN



## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """Load data from transmission_data.csv
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
        
    Returns
    -------
    dict
        transmission data
    """
    data = read_csv(os.path.join(data_dir,'transmission_data.csv'),
                    comment = '#',index_col = 0)
    data = data['value'].to_dict()
    data['Maximum savings ($/kWh)'] = float(data['Maximum savings ($/kWh)'])
    data['Distance to Community'] = float(data['Distance to Community'])
    #~ print data
    return data
                    
    
def load_project_details (data_dir):
    """load details related to exitign projects
    
    Parameters
    ----------
    data_dir: path
        path to data directory for community
    
    Returns
    -------
    dict
        a dictonary with the keys 'phase'(str), 
        'proposed capacity'(float), 'proposed generation'(float),
        'distance to resource'(float), 'generation capital cost'(float),
        'transmission capital cost'(float), 'operational costs'(float),
        'expected years to operation'(int),
    """
    tag = os.path.split(data_dir)[1].split('+')
    data_dir = os.path.join(os.path.split(data_dir)[0],tag[0])
    try:
        project_type = tag[1]
        if project_type != 'transmission':
            tag = None
        else:
            tag = '+'.join(tag[1:])
    except IndexError:
        tag = None
        
    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Transmission']

    if tag is None:
        # if no data make some
        yto = 5 # int(round(float(data['Reconnaissance'])))
        return {'phase': 'Reconnaissance',
                'proposed capacity': UNKNOWN,
                'proposed generation': UNKNOWN,
                'distance to resource': UNKNOWN,
                'generation capital cost': UNKNOWN,
                'transmission capital cost': UNKNOWN,
                'operational costs': UNKNOWN,
                'expected years to operation': yto,
                }
    
    # CHANGE THIS
    with open(os.path.join(data_dir, "transmission_projects.yaml"), 'r') as fd:
        dets = load(fd)[tag]
    
    # correct number years if nessary
    yto = dets['expected years to operation']
    if yto == UNKNOWN:
        try:
            yto = int(round(float(data[dets['phase']])))
        except TypeError:
            yto = 0
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = int(yto)
    
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'project details': load_project_details,
                    'nearest community':process_data_import,
                  }
