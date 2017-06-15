"""
Solar Power Preprocessing 
-------------------------

preprocessing functions for Solar Power component  

"""
import os.path
from pandas import read_csv
import numpy as np




def preprocess (preprocessor, **kwargs):
    """preprocess data solar power data in solar_resource_data.csv
    
    Parameters
    ----------
    preprocessor: preprocessor.Proprocessor
        a preprocessor object
        
    Returns
    -------
    dict
        preprocessed data
    
    """
    
    data = read_csv(
        os.path.join(preprocessor.data_dir,"solar_resource_data.csv"),
        comment = '#',
        index_col = 0
    )
        
    ids = [preprocessor.communities[0], preprocessor.aliases[0]]
    #~ if preprocessor.intertie_status == 'child':
        #~ ids = []
    
    solar_pv_output = \
        float(data.ix[ids][data.ix[ids].isnull().all(1) == False]\
        ['Output per 10kW Solar PV'])
    
    return {
        'Solar Power': {
            'enabled': True,
            'lifetime': 20,
            'start year': 2016,
            'average load limit': 50.0,
            'percent generation to offset': 15,
            
            'percent solar degradation': ((1 - .992) * 100),
            
            'output per 10kW solar PV': solar_pv_output,
            #~ 'road needed': False,
            #~ 'road needed for transmission line' : True,
            #~ 'transmission line distance': 0,
            
            
            'cost': 'UNKNOWN',
            'switch gear needed for solar': False,
            'cost per kW': 8000,
            #~ 'o&m cost per kWh': .02,
            'percent o&m': 1,
        }
    }
    
    
