"""
preprocessing.py

    preprocessing functions for Wind Power component  
"""
import os.path
from pandas import DataFrame, read_csv
import numpy as np
import shutil
from yaml import dump
from config import UNKNOWN

## List of raw data files required for wind power preproecssing 
raw_data_files = ['wind_class_assumptions.csv',
                  'wind_costs.csv',
                  "wind_data_existing.csv",
                  "wind_data_potential.csv",
                  "diesel_data.csv",
                  'wind_data_interties.csv',
                  "solar_data_existing.csv",
                  "wind_projects.csv",
                  'project_development_timeframes.csv']

## wind preprocessing functons 
def wind_preprocess_header (ppo):
    """
    wind preporcess header
    
    pre:
        ppo: a Preprocessor object
    post:
        returns the header for the wind data preprocessed csv file
    """
    ## TODO Expand
    return  "# " + ppo.com_id + " wind data\n"+ \
            ppo.comments_dataframe_divide
    
def wind_preprocess (ppo):
    """
    Reprocesses the wind data
    
    pre:
        ppo is a Preprocessor object. wind_class_assumptions, 
    wind_data_existing.csv and wind_data_potential.csv file exist at 
    ppo.data_dir's location 
    
    post:
        preprocessed wind data is saved at ppo.out_dir as wind_power_data.csv
    """
    try:
        existing = read_csv(os.path.join(ppo.data_dir,"wind_data_existing.csv"),
                        comment = '#',index_col = 0).ix[ppo.com_id]
        existing = existing['Rated Power (kW)']
    except KeyError:
        existing = 0
    #~ #~ print existing
    try:
        potential = read_csv(os.path.join(ppo.data_dir,
                                "wind_data_potential.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
    except KeyError:
        potential = DataFrame(index = ['Wind Potential','Wind-Resource',
                                       'Assumed Wind Class',
                                       'Wind Developability','Site Accessible ',
                                       'Permittability','Site Availability',
                                       'Load','Certainty',
                                       'Estimated Generation','Estimated Cost',
                                       'Note','Resource Note'])
                                       
    try:
        intertie = read_csv(os.path.join(ppo.data_dir,
                            "wind_data_interties.csv"),
                            comment = '#',
                            index_col = 0).ix[ppo.com_id+"_intertie"]
        intertie = int(intertie['Highest Wind Class on Intertie'])
    except KeyError:
        intertie = 0

    try:
        if intertie > int(potential['Assumed Wind Class']):
            potential.ix['Assumed Wind Class'] = intertie
            ppo.diagnostics.add_note("wind", 
                    "Wind class updated to max on intertie")
        
    except KeyError:
        pass
    
    assumptions = read_csv(os.path.join(ppo.data_dir,
                                "wind_class_assumptions.csv"),
                           comment = '#',index_col = 0)
                           
    try:
        solar_cap = read_csv(os.path.join(ppo.data_dir,
                                "solar_data_existing.csv"),
                            comment = '#',index_col = 0).ix[ppo.com_id]
        solar_cap = solar_cap['Installed Capacity (kW)']
        if np.isnan(solar_cap):
            solar_cap = 0
    except (IOError,KeyError):
        solar_cap = 0 
    
    try:
        capa = assumptions.ix[int(float(potential.ix['Assumed Wind Class']))]
        capa = capa.ix['REF V-VI Net CF']
    except (TypeError,KeyError):
        capa = 0
    #~ print capa
    
    #~ #~ print potential
    out_file = os.path.join(ppo.out_dir,"wind_power_data.csv")
    #~ #~ print ppo.out_dir,"wind_power_data.csv"
    fd = open(out_file,'w')
    fd.write(wind_preprocess_header(ppo))
    fd.write("key,value\n")
    fd.write("existing wind," + str(existing) +'\n')
    fd.write("existing solar," + str(solar_cap) + '\n')
    fd.write('assumed capacity factor,' +str(capa) +'\n')
    fd.close()

    #~ df = concat([ww_d,ww_a])
    potential.to_csv(out_file, mode = 'a',header=False)
    #~ self.wastewater_data = df
    ppo.MODEL_FILES['WIND_DATA'] = "wind_power_data.csv"
    
def copy_wind_cost_table(ppo):
    """
    copies wind cost table file to each community
    
    pre:
        ppo is a Preprocessor object. wind_costs.csv exists at ppo.data_dir
    post:
        wind_costs.csv is copied from ppo.data_dir to ppo.out_dir 
    """
    data_dir = ppo.data_dir
    out_dir = ppo.out_dir
    shutil.copy(os.path.join(data_dir,"wind_costs.csv"), out_dir)
    ppo.MODEL_FILES['WIND_COSTS'] = "wind_costs.csv"
## end wind preprocessing functions

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
    
    project_data = read_csv(os.path.join(ppo.data_dir,"wind_projects.csv"),
                           comment = '#',index_col = 0)
    
    project_data = DataFrame(ppo.get_communities_data(project_data))
    #~ print ppo.id_list
    #~ print project_data
    if len(project_data.T) == 1 :
        project_data = project_data.T


    for p_idx in range(len(project_data)):
        cp = project_data.ix[p_idx]
        
        p_name = cp['Project Name']
        try:
            if p_name == "" or np.isnan(p_name):
                p_name = "project_" + str(p_idx)
        except TypeError:
            p_name = "project_" + str(p_idx)
        p_name = 'wind+' + p_name
        
        phase = cp['Phase']
        proposed_capacity = cp['Proposed Capacity (kW)']
        proposed_generation = cp['Proposed Generation (kWh)']
        distance_to_resource = cp['Distance to Resource (ft)']
        generation_capital_cost = cp['Generation Capital Cost']
        transmission_capital_cost = cp['Transmission CAPEX']
        operational_costs = cp['Operational Costs / year']
        expected_years_to_operation = cp['Expected years to operation']
        if phase == "0":
            continue
        if phase == "Reconnaissance" and np.isnan(proposed_capacity) and\
           np.isnan(proposed_generation) and np.isnan(distance_to_resource) and\
           np.isnan(generation_capital_cost)  and \
           np.isnan(transmission_capital_cost) and \
           np.isnan(operational_costs) and \
           np.isnan(expected_years_to_operation):
            continue
        
        projects.append(p_name)
        
        proposed_capacity = float(proposed_capacity)
        if np.isnan(proposed_capacity):
            proposed_capacity = UNKNOWN
    
        proposed_generation = float(proposed_generation)
        if np.isnan(proposed_generation):
            proposed_generation = UNKNOWN
        
        distance_to_resource = float(distance_to_resource)
        if np.isnan(distance_to_resource):
            distance_to_resource = UNKNOWN
           
        generation_capital_cost = float(generation_capital_cost)
        if np.isnan(generation_capital_cost):
            generation_capital_cost = UNKNOWN
        
        transmission_capital_cost = float(transmission_capital_cost)
        if np.isnan(transmission_capital_cost):
            transmission_capital_cost = UNKNOWN
        
        operational_costs = float(operational_costs)
        if np.isnan(operational_costs):
            operational_costs = UNKNOWN
            
        expected_years_to_operation = float(expected_years_to_operation)
        if np.isnan(expected_years_to_operation):
            expected_years_to_operation = UNKNOWN
            
        p_data[p_name] = {'phase': phase,
                    'proposed capacity': proposed_capacity,
                    'proposed generation': proposed_generation,
                    'distance to resource': distance_to_resource,
                    'generation capital cost': generation_capital_cost,
                    'transmission capital cost': transmission_capital_cost,
                    'operational costs': operational_costs,
                    'expected years to operation': expected_years_to_operation
                        }
                            
    if len(p_data) != 0:
        fd = open(os.path.join(ppo.out_dir,"wind_projects.yaml"),'w')
        fd.write(dump(p_data,default_flow_style=False))
        fd.close()
    else:
        fd = open(os.path.join(ppo.out_dir,"wind_projects.yaml"),'w')
        fd.write("")
        fd.close()
        #~ return projects 


    ppo.MODEL_FILES['WIND_PROJECTS'] = "wind_projects.yaml"
    shutil.copy(os.path.join(ppo.data_dir,'project_development_timeframes.csv'), 
                ppo.out_dir)
    ppo.MODEL_FILES['TIMEFRAMES'] = 'project_development_timeframes.csv'
    #~ print ppo.MODEL_FILES
    return projects

## list of wind preprocessing functions
preprocess_funcs = [wind_preprocess, copy_wind_cost_table]