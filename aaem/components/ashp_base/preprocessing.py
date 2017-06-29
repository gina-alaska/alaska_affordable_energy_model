"""
Air Source Heat Pump preprocessing 
----------------------------------

    preprocessing functions for Air Source Heat Pump Base Component

"""
import os.path
from pandas import read_csv
import shutil

            
## preprocess the existing projects
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
    comp_name = kwargs['ashp_type']
    cost_per_btu_hrs = kwargs['ashp_cost_per_btu_hrs']
    btu_hrs = kwargs['ashp_btu_hrs']
    
    start_year = preprocessor.data['community']['current year'] + 1
    
    data = read_csv(
        os.path.join(preprocessor.data_dir, "ashp_climate_data.csv"),
        comment = '#',
        index_col = 0
    )
    ids = [preprocessor.communities[0],preprocessor.aliases[0]]
    if preprocessor.intertie_status == 'child':
        ids = [preprocessor.communities[1],preprocessor.aliases[1]]
    climate_data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
    climate_data =  climate_data.T
    climate_data.columns = ['value']
    climate_data.index.name = 'key'
    performance_data = read_csv(
        os.path.join(preprocessor.data_dir,'ashp_perfromance_data.csv')
    )
    return {
        comp_name: {
            'enabled': True, # 
            'lifetime': 15, # number years <int>
            'start year': start_year, # start year <int>
            'btu/hrs': btu_hrs,
            'cost per btu/hrs': cost_per_btu_hrs,
            'o&m per year': 320,
            
            'data': climate_data,
            'perfromance data': {
                'COP': performance_data['COP'].tolist(),
                'Temperature': performance_data['Temperature'].tolist(),
                'Percent of Total Capacity': 
                    performance_data['Percent of Total Capacity'].tolist()
            }
            
        }
    }
