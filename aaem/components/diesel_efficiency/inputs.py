"""
Diesel Efficiency inputs
------------------------

input functions for Diesel Efficiency component
    
"""
import os.path
from pandas import read_csv

## Functions for CommunityData IMPORT keys
def process_data_import(data_dir):
    """reads input data from "diesel_data.csv"
        
    Parameters
    ----------
    data_dir : path
        the path to the input data directory
    
    Returns
    -------
    dict
        diesel power house data
    """
    data_file = os.path.join(data_dir, "diesel_powerhouse_data.csv")
    data = read_csv(data_file, comment = '#', index_col=0, header=0)
    return data['value'].to_dict()
    
#~ def load_project_details (data_dir):
    #~ """
    #~ load details related to exitign projects
    
    #~ pre:
        #~ data_dir is a directory with  'project_development_timeframes.csv',
        #~ and "project_name_projects.yaml" in it 
    
    #~ post:
        #~ retunrns a dictonary wht the keys 'phase'(str), 
        #~ 'proposed capacity'(float), 'proposed generation'(float),
        #~ 'distance to resource'(float), 'generation capital cost'(float),
        #~ 'transmission capital cost'(float), 'operational costs'(float),
        #~ 'expected years to operation'(int),
    #~ """
    #~ try:
        #~ tag = os.path.split(data_dir)[1].split('+')
        #~ project_type = tag[1]
        #~ tag = tag[1] + '+' +tag[2]
        #~ if project_type != PROJECT_TYPE:
            #~ tag = None
    #~ except IndexError:
        #~ tag = None
        
    #~ # TODO fix no data in file?
    #~ # data_file = os.path.join(data_dir, 'project_development_timeframes.csv')
    #~ #data = read_csv(data_file, comment = '#',
                    #~ # index_col=0, header=0)[PROJECT_TYPE]

    #~ if tag is None:
        #~ # if no data make some
        #~ yto = 3#int(round(float(data['Reconnaissance'])))
        #~ return {'phase': 'Reconnaissance',
                #~ 'capital costs': UNKNOWN,
                #~ 'operational costs': UNKNOWN,
                #~ 'expected years to operation': yto,
                #~ }
    
    #~ # CHANGE THIS
    
    #~ with open(os.path.join(data_dir, "COPMPONENT_PROJECTS.yaml"), 'r') as fd:
        #~ dets = load(fd)[tag]
    
    #~ # correct number years if nessary
    #~ yto = dets['expected years to operation']
    #~ if yto == UNKNOWN:
        #~ try:
            #~ yto = int(round(float(data[dets['phase']])))
        #~ except TypeError:
            #~ yto = 0
        #~ dets['expected years to operation'] = yto
    #~ dets['expected years to operation'] = int(yto)
    
    #~ return dets
    
#~ ## library of keys and functions for CommunityData IMPORT Keys
yaml_import_lib = {'data':process_data_import}
