"""
Heat Recovery inputs
--------------------

input functions for Heat Recovery component
    
    
"""
import os.path
from pandas import read_csv
from config import UNKNOWN, PROJECT_TYPE
from yaml import load

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """convert input data to useable form
    
    Parameters
    ----------
        data_dir : path
            the path to the input data directory
            
    Returns
    -------
        heat recovery project data as a dictonary
    
    """
    #~ return {}
    #~ try:
    data_file = os.path.join(data_dir, "heat_recovery_projects_potential.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    #~ except:
        #~ return {}
    
def load_project_details (data_dir):
    """load details related to exitign projects
    
    Parameters
    ----------
        data_dir : path
            the path to the input data directory
    
    Returns
    -------
        retunrns a dictonary wht the keys 'phase'(str), 
        'proposed capacity'(float), 'proposed generation'(float),
        'distance to resource'(float), 'generation capital cost'(float),
        'transmission capital cost'(float), 'operational costs'(float),
        'expected years to operation'(int)
    """
    tag = os.path.split(data_dir)[1].split('+')
    data_dir = os.path.join(os.path.split(data_dir)[0],tag[0])
    try:
        project_type = tag[1]
        if project_type != PROJECT_TYPE:
            tag = None
        else:
            tag = '+'.join(tag[1:])
    except IndexError:
        tag = None

    # get the estimated years to operation
    # CHANGE THIS Replace the PROJECT_TYPE with the type of the project
    data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    data = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Heat Recovery']

    if tag is None:
        # if no data make some
        yto = 0
        return {'name': 'None', 
                'phase': 'Reconnaissance',
                'project type': 'New',
                'total feet piping needed': UNKNOWN, 
                'number buildings': UNKNOWN,
                'buildings': [],
                'proposed gallons diesel offset': UNKNOWN,
                'proposed Maximum btu/hr': UNKNOWN, 
                'capital costs': UNKNOWN,
                'expected years to operation': yto
                }
    
    
    # CHANGE THIS
    with open(os.path.join(data_dir, "heat_recovery_projects.yaml"), 'r') as fd:
        dets = load(fd)[tag]
    
    # correct number years if nessary
    yto = dets['expected years to operation']
    if yto == UNKNOWN:
        try:
            yto = int(round(float(data[dets['phase']])))
        except (TypeError, KeyError):
            if dets['phase'] == "CDR":
                yto = int(round(float(data['Design'])))
            else:
                yto = 0
        dets['expected years to operation'] = yto
    dets['expected years to operation'] = int(yto)
    #~ print dets
    return dets
    
## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'project details': load_project_details,
                   'estimate data': process_data_import }# fill in
    
