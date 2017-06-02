"""
Hydropower preprocessing 
------------------------

preprocessing functions for Diesel Efficiency component  

"""
import os.path
from pandas import DataFrame, read_csv
from config import UNKNOWN
from yaml import dump
import shutil
import copy

## preprocess the existing projects
def preprocess (preprocessor, **kwargs):
    """preprocess data related to existing projects
    
    Parameters
    ----------
    preprocessor: preprocessor.Proprocessor
        a preprocessor object
        
    Returns
    -------
    list
        project names
    
    """
    base = {
        'Hydropower': {
            'enabled': True,
            'start year': 2016,
            'lifetime': 50,
            
            'name': 'none',
            'phase': 'none',
            'proposed capacity': 'none',
            'proposed generation': 'none',
            'generation capital cost': 'none',
            'transmission capital cost': 'none',
            'expected years to operation': 'none',
            'source': 'none',
            
            'percent o&m': 1,
            'percent heat recovered': 15,
        }
    }
    if preprocessor.intertie_status == 'child':
        return base
    if preprocessor.intertie_status == 'parent' and\
        preprocessor.process_intertie == False:
        return base
    
    projects = []
    p_data = {}
 
    project_data = read_csv(os.path.join(preprocessor.data_dir,
        "hydro_projects_potential.csv"),
        comment = '#',index_col = 0)
        
    data_file = os.path.join(
        preprocessor.data_dir,
        'project_development_timeframes.csv'
    )
    timeframes = read_csv(data_file, comment = '#',
                    index_col=0, header=0)['Hydroelectric']
    
    
    ids = preprocessor.communities + preprocessor.aliases
    if preprocessor.intertie_status == 'child':
        ids = []
        
    #~ print ids
    
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
        
    names = []
    #~ print project_data
    for p_idx in range(len(project_data)):
        cp = project_data.iloc[p_idx]
        
        #~ print '--------'
        #~ print cp.values
        #~ print '--------'
        
        p_name = 'hydro+project_' + str(p_idx) 
        if cp.name not in \
            [preprocessor.communities[0], preprocessor.aliases[0]]:
            p_name +=  '_' + cp.name
            
        phase = cp['Phase Completed']
        try:
            phase = phase[0].upper() + phase[1:]
        except TypeError:
            preprocessor.diagnostics.add_note('Hydropower Projects', 
                                        'missing value assuming Reconnaissance')
            phase = 'Reconnaissance'
        
            
        
        proposed_capacity = float(cp['AAEM Capacity (kW)'])
        proposed_generation = float(cp['AAEM Generation (kWh)'])
        #~ distance_to_resource = float(cp['Distance'])
        generation_capital_cost = float(cp['Construction Cost (2014$)'])
        transmission_capital_cost = float(cp['Transmission Cost (current)'])
        source = cp['Source']
        #~ expected_years_to_operation = UNKNOWN
        if phase == "0":
            preprocessor.diagnostics.add_note('Hydropower Projects', 
                                            '"0" corrected to Reconnaissance')
            phase = "Reconnaissance"
            
        try:
            yto = int(round(float(timeframes[phase])))
        except (TypeError, KeyError):
            yto = 0
        
        start_year = base['Hydropower']['start year'] + yto

        projects.append(p_name)
        #actual name
        a_name = str(cp['Project'])
        if a_name.find(str(cp['Stream'])) == -1 and str(cp['Stream']) != 'nan':
            a_name += ' -- ' + str(cp['Stream'])
        #~ print a_name
        a_name = \
            '"' + a_name.decode('unicode_escape').encode('ascii','ignore') + '"'
        #~ print a_name
        project = copy.deepcopy(base)
        project['Hydropower'].update({
            'start year': start_year,
            'name': a_name,
            'phase': phase,
            'proposed capacity': proposed_capacity,
            'proposed generation': proposed_generation,
            'generation capital cost': generation_capital_cost,
            'transmission capital cost': transmission_capital_cost,
            #~ 'expected years to operation': expected_years_to_operation,
            'source':source
        })
        #~ print project 
        p_data[p_name] = project 
        #~ print p_data[p_name] 

    
    p_data['no project'] = base
    #~ print p_data
    return p_data
    


