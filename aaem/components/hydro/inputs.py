"""
inputs.py

    input functions for Hydropower component
"""
import os.path
from pandas import read_csv
from config import UNKNOWN
from yaml import load

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """
    """
    pass
    
def load_project_details (data_dir):
    """
    load details related to exitign projects
    
    pre:
        data_dir is a directory with  'project_development_timeframes.csv',
        and "project_name_projects.yaml" in it 
    
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
        if project_type != 'hydro':
            tag = None
    except IndexError:
        tag = None
    
        
    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Hydroelectric']

    if tag is None:
        # if no data make some
        yto = 5#int(round(float(data['Reconnaissance'])))
        return None
            #~ {'phase': 'Reconnaissance',
                #~ 'proposed capacity': 25,
                #~ 'proposed generation': 1000,
                #~ 'distance to resource': 10,
                #~ 'generation capital cost': 500,
                #~ 'transmission capital cost': 500,
                #~ 'expected years to operation': yto,
                #~ }

    
    # CHANGE THIS
    with open(os.path.join(data_dir, "hydro_projects.yaml"), 'r') as fd:
        dets = load(fd)[tag]
    
    # correct number years if nessary
    yto = dets['expected years to operation']
    if yto == UNKNOWN:
        try:
            yto = int(round(float(data[dets['phase']])))
        except (TypeError, KeyError):
            yto = 0
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = int(yto)
    
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'project details': load_project_details}
