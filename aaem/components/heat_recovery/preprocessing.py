"""
Heat Recovery preprocessing 
---------------------------

preprocessing functions for Heat Recovery component  

"""
import os.path
import numpy as np
from pandas import DataFrame, read_csv
import shutil
from yaml import dump

from config import UNKNOWN

import copy


def preprocess (preprocessor, **kwargs):
    """preprocess data related to existing projects
    
    Parameters
    ----------
    preprocessor: preprocessor.Preprocessor
        a preprocessor object
        
    Returns
    -------
    list
        project names
    
    """
    #~ data = read_csv(
        #~ os.path.join(ppo.data_dir,"heat_recovery_projects_potential.csv"), 
        #~ comment = '#',
        #~ index_col = 0
    #~ )
    #~ ids = [preprocessor.communities[0], preprocessor.aliases[0]]
    #~ if preprocessor.intertie_status == 'child':
        #~ ids = [preprocessor.communities[1], preprocessor.aliases[1]]
                                        
    #~ data = data.ix[ids][data.ix[ids].isnull().all(1) == False]

    #~ data_cols_in = ['HR Functioning as of November 2016 (Yes/No)',
                    #~ 'Identified as priority by HR working group',
                 #~ 'Est. current annual heating fuel gallons displaced',
                 #~ 'Proposed Gallons of Diesel Offset']
    #~ data =  data[data_cols_in]
    #~ data.columns = data_cols
    #~ data = []
    # if no data add defaults
    #~ if len(data) == 0:
        #~ data = DataFrame([['No','No', np.nan, np.nan],],columns = data_cols)
    
    #~ # if multiple data rows assume first is best
    #~ if len(data) > 1:
        #~ data = data.iloc[0]

    base = {
        'Heat Recovery' : {
            'enabled': True,
            'lifetime': 20, # number years <int>
            'start year': 2016, # start year <int>
            
            
            'est. current annual heating fuel gallons displaced': UNKNOWN,
            
            'estimate pipe distance': 1500,
            'estimate pipe cost/ft': 135,
            'estimate buildings to heat': 2,
            'heating conversion efficiency': 0.75,
            'percent heat recovered': 10,
            'estimate cost/building': 40000,
            'o&m per year': 500,
            
            'name': UNKNOWN,
            'phase': 'Reconnaissance',
            'identified as priority': UNKNOWN,
            'project type': UNKNOWN,
            'capital costs': UNKNOWN,
            'number buildings': UNKNOWN,
            'buildings': [],
            'total feet piping needed': UNKNOWN,
            'proposed maximum btu/hr': UNKNOWN,
            'proposed gallons diesel offset': UNKNOWN,
            'link': 'none',
            'notes': 'none',
            
            
        }
    }
    if preprocessor.process_intertie == True:
        return base
    p_data = {}
 
    proj_cols = [
        'Project Name', 'Year of Feasibility Study Completion', 
        'Phase Completed', 'New/Repair/Extension',
        'Total Round-trip Distance of Piping (feet)', 
        'Number of Buildings/Facilities', 'Buildings/Facilities to be Served',
        'Proposed Gallons of Diesel Offset', 'Proposed Maximum Btu/hr',
        'Total CAPEX', 'Source', 'Link', 'Notes', 
        'Est. current annual heating fuel gallons displaced',
        'Identified as priority by HR working group'
        ]
    project_data = read_csv(
        os.path.join(
            preprocessor.data_dir, 
            "heat_recovery_projects_potential.csv"
        ),
        comment = '#',
        index_col = 0
    )[proj_cols]
    
    
        
    data_file = os.path.join(
        preprocessor.data_dir,
        'project_development_timeframes.csv'
    )
    timeframes = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Heat Recovery']
    
    
    ids = [preprocessor.communities[0], preprocessor.aliases[0]]
    if preprocessor.intertie_status == 'child':
        ids = [preprocessor.communities[1], preprocessor.aliases[1]]
    
    current = \
        project_data['Est. current annual heating fuel gallons displaced']\
        [project_data.isnull().all(1) == False]
    try:
        float(current)
        base['Heat Recovery']\
            ['est. current annual heating fuel gallons displaced'] = current
    except:
        pass
        
    
    del project_data['Est. current annual heating fuel gallons displaced']
    
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
        
    
    if len(project_data) == 1 and \
        not type(project_data.iloc[0]['Project Name']) is str:
        return base

    for p_idx in range(len(project_data)):
        cp = project_data.iloc[p_idx]
        p_name = 'heat_recovery+project_' + str(p_idx)
        
        name = str(cp['Project Name'])
        
        priority = str(cp['Identified as priority by HR working group']) 
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
        #~ print capex
        #~ expected_years_to_operation = UNKNOWN
        if phase == "0":
            preprocessor.diagnostics.add_note(
                'Heat Recovery', 
                'phase "0" corrected to Reconnaissance'
            )
            phase = "Reconnaissance"
            
        try:
            yto = int(round(float(timeframes[phase])))
        except (TypeError, KeyError):
            yto = 0
        
        start_year = preprocessor.data['community']['current year'] + yto

        project = copy.deepcopy(base)
        
        project['Heat Recovery']['start year'] = start_year
        project['Heat Recovery']['name'] =  name
        project['Heat Recovery']['phase'] =  phase
        project['Heat Recovery']['identified as priority'] =  priority
        project['Heat Recovery']['project type'] =  project_type
        project['Heat Recovery']['capital costs'] = capex
        project['Heat Recovery']['total feet piping needed'] =  total_piping_needed
        project['Heat Recovery']['number buildings'] =  num_buildings
        project['Heat Recovery']['buildings'] =  buildings
        project['Heat Recovery']['proposed gallons diesel offset'] = diesel_offset
        project['Heat Recovery']['proposed maximum btu/hr'] =  max_btu_per_hr
        project['Heat Recovery']['link'] = cp['Link']
        project['Heat Recovery']['notes'] = cp['Notes']

        #~ print project 
        p_data[p_name] = project  

    
    p_data['no project'] = base

    return p_data


