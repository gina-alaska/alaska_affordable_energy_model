"""
preprocessing.py

    preprocessing functions for Transmission Line component  
"""
import os.path
from pandas import read_csv
import numpy as np

## List of raw data files required for wind power preproecssing 
raw_data_files = [#"transmission_projects.csv",
                  'project_development_timeframes.csv',
                  'transmission_distances.csv',
                  ]

## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " Transmission data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    
    """
    #CHANGE THIS
    out_file = os.path.join(ppo.out_dir,"transmission_data.csv")

    data = read_csv(os.path.join(ppo.data_dir,'transmission_distances.csv'),
                    comment = '#',index_col = 0)
                    
    
    #~ try:
    data = ppo.get_communities_data(data)
    #~ except KeyError:
        #~ data
    
    #~ print data
    try:
        max_savings = float(data['Maximum savings ($/kWh)'])
        nearest_comm = data['Nearest Community with Lower Price Power']
        nearest_comm = str(nearest_comm.values[0])
        if 'nan' == nearest_comm:
            nearest_comm = ''
        distance = float(data['Distance to Community'])
    except TypeError:
        max_savings = np.nan
        nearest_comm = np.nan
        distance = np.nan
    
    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write('key,value\n')
    fd.write('Maximum savings ($/kWh),' + str(max_savings) +'\n')
    fd.write('Nearest Community with Lower Price Power,' \
                                        + str(nearest_comm) +'\n')
    fd.write('Distance to Community,' + str(distance ) +'\n')
    fd.close()
    
    # create data and uncomment this
    #~ data.to_csv(out_file, mode = 'a',header=False)
    
    ppo.MODEL_FILES['TRANSMISSION_DATA'] = "transmission_data.csv" # CHANGE THIS
    
## list of wind preprocessing functions
preprocess_funcs = [preprocess]

## preprocess the existing projects
### This function is called differently from the other preprocessor functions,
### so it does not need to be added to preprocess_funcs
def preprocess_existing_projects (ppo):
    """
    preprocess data related to existing projects
    
    pre:
        ppo is a is a Preprocessor object. "wind_projects.csv" and 
        'project_development_timeframes.csv' exist in the ppo.data_dir 
    post:
        data for existing projets is usable by model
    """
    projects = []
    p_data = {}
    
    #~ ## CHANGE THIS
    #~ project_data = read_csv(os.path.join(ppo.data_dir,
                            #~ "transmission_projects.csv"),
                            #~ comment = '#',index_col = 0)
    
    #~ project_data = DataFrame(project_data.ix[ppo.com_id])
    #~ if len(project_data.T) == 1 :
        #~ project_data = project_data.T

    #~ ## FILL IN LOOP see function in wind _power.py for an example
    #~ for p_idx in range(len(project_data)):
       #~ pass
    
    #~ with open(os.path.join(ppo.out_dir,"transmission_projects.yaml"),'w') as fd:
        #~ if len(p_data) != 0:
            #~ fd.write(dump(p_data,default_flow_style=False))
        #~ else:
            #~ fd.write("")
        
    #~ ## CHANGE THIS
    #~ ppo.MODEL_FILES['TRANSMISSION_PROJECTS'] = "transmission_projects.yaml"
    #~ shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                #~ ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects

