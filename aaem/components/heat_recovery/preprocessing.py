"""
preprocessing.py

    preprocessing functions for Heat Recovery component  
"""
import os.path
import numpy as np
from pandas import DataFrame, read_csv
import shutil
from yaml import dump

from config import UNKNOWN

## List of raw data files required for wind power preproecssing 
raw_data_files = ["heat_recovery_data.csv",
                  'project_development_timeframes.csv']

## preprocessing functons 
def preprocess_header (ppo):
    """
    """
    return  "# " + ppo.com_id + " heat recovery data\n"+ \
            ppo.comments_dataframe_divide
    
def preprocess (ppo):
    """
    
    """
    #CHANGE THIS
    out_file = os.path.join(ppo.out_dir,"heat_recovery_data.csv")

    data = read_csv(os.path.join(ppo.data_dir,"heat_recovery_data.csv"), 
                                    comment = '#',index_col = 0)
                                    
    data = ppo.get_communities_data(data)
    data_cols = ['Waste Heat Recovery Opperational','Add waste heat Avail',
                 'Est. current annual heating fuel gallons displaced',
                 'Est. potential annual heating fuel gallons displaced']
    data =  data[data_cols]
    
    # if no data add defaults
    if len(data) == 0:
        data = DataFrame([['No','No', np.nan, np.nan],],columns = data_cols)
    
    # if multiple data rows assume first is best
    if len(data) > 1:
        data = data.iloc[0]


    data['Waste Heat Recovery Opperational'] = \
        data['Waste Heat Recovery Opperational'].fillna('No')
    data['Add waste heat Avail'] = data['Add waste heat Avail'].fillna('No')
    
    data = data.T

    
    fd = open(out_file,'w')
    fd.write(preprocess_header(ppo))
    fd.write("key,value\n")
    fd.close()

    
    
    # create data and uncomment this
    data.to_csv(out_file, mode = 'a', header=False)
    
    ppo.MODEL_FILES['HR_DATA'] = "heat_recovery_data.csv" # CHANGE THIS
    
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
    
    proj_cols = ['Project Name','Year','Phase Completed',
                 'New/Repair/Extension',
                 'Total Round-trip Distance of Piping (feet)',
                 'Number of Buildings/Facilities',
                 'Buildings/Facilities to be Served',
                 'Proposed Gallons of Diesel Offset',
                 'Proposed Maximum Btu/hr','Total CAPEX','Source']
    project_data = read_csv(os.path.join(ppo.data_dir,
                                "heat_recovery_data.csv"),
                            comment = '#',index_col = 0)[proj_cols]
                            
    project_data = ppo.get_communities_data(project_data)
    if len(project_data) != 0 and int(project_data.fillna(0).sum(axis=1)) == 0:
        project_data = DataFrame(columns=project_data.columns)
    #~ print project_data

    for p_idx in range(len(project_data)):
        cp = project_data.ix[p_idx]
        p_name = 'heat_recovery+project_' + str(p_idx)
        
        name = str(cp['Project Name'])
        phase = str(cp['Phase Completed'])
        phase = phase[0].upper() + phase[1:]
        project_type = str(cp['New/Repair/Extension'])
        total_piping_needed = \
            float(cp['Total Round-trip Distance of Piping (feet)'])
        num_buildings = int( cp['Number of Buildings/Facilities'] )
        buildings = str(cp['Buildings/Facilities to be Served']).split(',')
        
        diesel_offset = float(cp['Proposed Gallons of Diesel Offset'])
        max_btu_per_hr = float(cp['Proposed Maximum Btu/hr'])
        capex = float(cp['Total CAPEX'])
        
        
        expected_years_to_operation = UNKNOWN
        
        projects.append(p_name)
        
        p_data[p_name] = {'name': name, 
                          'phase': phase,
                          'project type': project_type,
                          'total feet piping needed': total_piping_needed, 
                          'number buildings': num_buildings,
                          'buildings': buildings,
                          'proposed gallons diesel offset':diesel_offset,
                          'proposed Maximum btu/hr': max_btu_per_hr, 
                          'captial costs':capex,
                          'expected years to operation':
                                                expected_years_to_operation
                        }
        
        
    
    with open(os.path.join(ppo.out_dir,
                    "heat_recovery_projects.yaml"),'w') as fd:
        if len(p_data) != 0:
            fd.write(dump(p_data,default_flow_style=False))
        else:
            fd.write("")
        
    ## CHANGE THIS
    ppo.MODEL_FILES['HR_PROJECTS'] = "heat_recovery_projects.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects


