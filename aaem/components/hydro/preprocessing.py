"""
preprocessing.py

    preprocessing functions for Hydropower component  
"""
import os.path
from pandas import DataFrame, read_csv
from config import UNKNOWN
from yaml import dump
import shutil

## List of raw data files required for wind power preproecssing 
raw_data_files = ["hydro_project_potentials.csv",
                  'project_development_timeframes.csv']

## all preprocessing is for existing projects
preprocess_funcs = [] 

## preprocess the existing projects
def preprocess_existing_projects (ppo):
    """
    preprocess data related to existing projects
    
    pre:
        ppo is a is a Preprocessor object. "wind_projects_potential.csv" and 
        'project_development_timeframes.csv' exist in the ppo.data_dir 
    post:
        data for existing projets is usable by model
    """
    projects = []
    p_data = {}
    
    ## CHANGE THIS
    project_data = read_csv(os.path.join(ppo.data_dir,"hydro_projects_potential.csv"),
                           comment = '#',index_col = 0)
    
    try:
        project_data = DataFrame(project_data.ix[ppo.com_id])
        if len(project_data.T) == 1 :
            project_data = project_data.T
    except KeyError:
        project_data = []

    #~ ## FILL IN LOOP see function in wind _power.py for an example
    names = []
    for p_idx in range(len(project_data)):
        cp = project_data.ix[p_idx]
        p_name = 'hydro+project_' + str(p_idx) #+ str(cp['Project']).replace(' ','_').replace('/','-').replace(';','').replace('.','').replace("'",'').replace('_-_','_').replace(',','').replace('(','').replace(')','')
        #~ i = 1
        #~ i = 1
        #~ while (p_name in names):
            #~ p_name = 'hydro+' + str(cp['Project']).replace(' ','_').replace('/','-').replace(';','').replace('.','').replace("'",'').replace('_-_','_').replace(',','').replace('(','').replace(')','') + '_' + str(i)
            #~ i += 1
        #~ names.append(p_name)

        
        phase = cp['Phase Completed']
        try:
            phase = phase[0].upper() + phase[1:]
        except TypeError:
            ppo.diagnostics.add_note('Hydropower Projects', 
                                        'missing value assuming Reconnaissance')
            phase = 'Reconnaissance'
        proposed_capacity = float(cp['AAEM Capacity (kW)'])
        proposed_generation = float(cp['AAEM Generation (kWh)'])
        #~ distance_to_resource = float(cp['Distance'])
        generation_capital_cost = float(cp['Construction Cost (2014$)'])
        transmission_capital_cost = float(cp['Transmission Cost (current)'])
        expected_years_to_operation = UNKNOWN
        if phase == "0":
            ppo.diagnostics.add_note('Hydropower Projects', 
                                            '"0" corrected to Reconnaissance')
            phase = "Reconnaissance"
            

        projects.append(p_name)
        #actual name
        a_name = str(cp['Project'])
        if a_name.find(str(cp['Stream'])) == -1 and str(cp['Stream']) != 'nan':
            a_name += ' -- ' + str(cp['Stream'])
            
        p_data[p_name] = {'name': a_name,
                    'phase': phase,
                    'proposed capacity': proposed_capacity,
                    'proposed generation': proposed_generation,
                    #~ 'distance to resource': distance_to_resource,
                    'generation capital cost': generation_capital_cost,
                    'transmission capital cost': transmission_capital_cost,
                    'expected years to operation': expected_years_to_operation
                        }
    
    with open(os.path.join(ppo.out_dir,"hydro_projects.yaml"),'w') as fd:
        if len(p_data) != 0:
            fd.write(dump(p_data,default_flow_style=False))
        else:
            fd.write("")
        
    ## CHANGE THIS
    ppo.MODEL_FILES['COMPONENT_PROJECTS'] = "hydro_projects.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects


