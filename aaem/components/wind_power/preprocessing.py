"""
Wind power Preprocessing 
------------------------

preprocessing functions for The Wind Power component  

"""
import os.path
from pandas import DataFrame, read_csv
import numpy as np
import shutil
from yaml import dump
from config import UNKNOWN
import aaem.constants as constants
import copy
    
def preprocess (preprocessor, **kwargs):
    """preprocess wind power data 
    
    Parameters
    ----------
    preprocessor: preprocessor.Preprocessor
        a preprocessor object
        
    Returns
    -------
    dict
        preprocessed data
    
    """

    wind_classes = read_csv(
        os.path.join(preprocessor.data_dir, "wind_classes.csv"),
        comment = '#',
        index_col = 0
    )
                            
    ids = preprocessor.communities + preprocessor.aliases
    wind_class = wind_classes.ix[ids]['Assumed Wind Class'].max()
    preprocessor.diagnostics.add_note( 'Wind Power',
        'Using max wind class for all communities in intertie')
    if np.isnan(wind_class):
        wind_class = 0
        preprocessor.diagnostics.add_warning( 'Wind Power',
        'No wind class found, setting wind class to 0')
    
    assumptions = read_csv(
        os.path.join(preprocessor.data_dir, "wind_class_cf_assumptions.csv"),
        comment = '#',
        index_col = 0
    )
                           
    try:
        capa = assumptions.ix[int(float(wind_class))].ix['REF V-VI Net CF']
    except (TypeError,KeyError):
        preprocessor.diagnostics.add_warning( 'Wind Power',
        'No wind class found, setting capacity factor to 0')
        capa = 0
        
    distance = 1
    
    estimated_costs = read_csv(
        os.path.join(preprocessor.data_dir,'wind_kw_costs.csv'),
        index_col = 0
    )
    # road needed assumed, otherwise it would be 250000
    transmission_line_cost = 500000 

    base = {
        'Wind Power': {
            'enabled': True,
            'lifetime': 20, 
            'start year': 2019,
            'average load limit': 100.0,
            'percent generation to offset': 150,
            
            'name': '',
            'source': '',
            'notes': '',
            'proposed capacity': UNKNOWN,
            'generation capital cost': UNKNOWN,
            'operational costs': UNKNOWN,
            'phase': 'Reconnaissance',
            'proposed generation': UNKNOWN,
            'distance to resource': distance, 
            'transmission capital cost': UNKNOWN,
            
            
            'wind class': wind_class,
            'capacity factor': capa,
            'percent heat recovered': 20,
            'secondary load': True,
            
            
            'secondary load cost': 200000, # 
            'percent o&m': 1,
            'estimated costs': estimated_costs,
            'est. transmission line cost': transmission_line_cost,
        }
    }

    p_data = {}
 
    project_data = read_csv(os.path.join(preprocessor.data_dir,
        "wind_projects_potential.csv"),
        comment = '#',index_col = 0)
        
    data_file = os.path.join(
        preprocessor.data_dir,
        'project_development_timeframes.csv'
    )
    timeframes = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Wind']
    
    ids = preprocessor.communities + preprocessor.aliases
    if preprocessor.intertie_status == 'child':
        ids = []
    try:
        project_data = project_data.ix[ids]
        #~ print project_data
        project_data = \
            project_data[project_data.isnull().all(1) == False]
        if len(project_data.T) == 1 :
            project_data = project_data.T
    except (ValueError, KeyError) as e:
        #~ print e
        project_data = []
        
    for p_idx in range(len(project_data)):
        cp = project_data.iloc[p_idx]

        
        p_name = 'wind+project_' + str(p_idx) 
        if cp.name not in \
            [preprocessor.communities[0], preprocessor.aliases[0]]:
            p_name +=  '_' + cp.name
        
        phase = cp['Phase']
        try:
            phase = phase[0].upper() + phase[1:]
            if phase == "0":
                preprocessor.diagnostics.add_note('Wind Power Projects', 
                                            '"0" corrected to Reconnaissance')
                phase = "Reconnaissance"
        except TypeError:
            preprocessor.diagnostics.add_note('Wind Power Projects', 
                                        'missing value assuming Reconnaissance')
            phase = 'Reconnaissance'
        
       
        proposed_capacity = cp['Proposed Capacity (kW)']
        proposed_generation = cp['Proposed Generation (kWh)']
        distance_to_resource = cp['Distance to Resource (ft)']
        generation_capital_cost = cp['Generation Capital Cost']
        transmission_capital_cost = cp['Transmission CAPEX']
        operational_costs = cp['Operational Costs / year']

        name = str(cp['Project Name'])
        source = str(cp['link'])
        notes = str(cp['notes'])


        try:
            if phase == "Reconnaissance" and np.isnan(proposed_capacity) and\
               np.isnan(proposed_generation) and \
               np.isnan(distance_to_resource) and\
               np.isnan(generation_capital_cost)  and \
               np.isnan(transmission_capital_cost) and \
               np.isnan(operational_costs) and \
               np.isnan(expected_years_to_operation):
                continue
        except TypeError:
            continue
        
        #~ projects.append(p_name)
        
        try:
            proposed_capacity = float(proposed_capacity)
            if np.isnan(proposed_capacity):
                proposed_capacity = UNKNOWN
        except ValueError:
            proposed_capacity = UNKNOWN
    
        try:
            proposed_generation = float(proposed_generation)
            if np.isnan(proposed_generation):
                proposed_generation = UNKNOWN
        except ValueError:
            proposed_generation = UNKNOWN
        
        try:
            distance_to_resource = \
                float(distance_to_resource) * constants.feet_to_mi
            if np.isnan(distance_to_resource):
                distance_to_resource = distance
        except ValueError:
            distance_to_resource = distance
           
        try:
            generation_capital_cost = float(generation_capital_cost)
            if np.isnan(generation_capital_cost):
                generation_capital_cost = UNKNOWN
        except ValueError:
            generation_capital_cost = UNKNOWN
        
        try:
            transmission_capital_cost = float(transmission_capital_cost)
            if np.isnan(transmission_capital_cost):
                transmission_capital_cost = UNKNOWN
        except ValueError:
            transmission_capital_cost = UNKNOWN
        
        try:
            operational_costs = float(operational_costs)
            if np.isnan(operational_costs):
                operational_costs = UNKNOWN
        except ValueError:
            operational_costs = UNKNOWN
        
        #~ expected_years_to_operation = UNKNOWN
        
        try:
            yto = int(round(float(timeframes[phase])))
        except (TypeError, KeyError):
            yto = 0
        preprocessor.data['community']['current year']
        start_year = preprocessor.data['community']['current year'] + yto

        project = copy.deepcopy(base)
        project['Wind Power'].update({
            'name': name,
            'source': source,
            'notes': notes,
            'start year': start_year,
            'phase': phase,
            'proposed capacity': proposed_capacity  ,
            'generation capital cost': generation_capital_cost,
            'operational costs': operational_costs,
            'proposed generation': proposed_generation ,
            'distance to resource': distance_to_resource,
            'transmission capital cost': transmission_capital_cost ,
        })
        #~ print project 
        p_data[p_name] = project 
        #~ print p_data[p_name] 

    
    p_data['no project'] = base
    #~ print p_data
    return p_data
