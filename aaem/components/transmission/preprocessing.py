"""
Transmission Preprocessing 
--------------------------

preprocessing functions for The Transmission component  

"""
import os.path
from pandas import read_csv
import numpy as np

    
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
    data = read_csv(
        os.path.join(preprocessor.data_dir,'transmission_distances.csv'),
        comment = '#',
        index_col = 0)
      
                
    if not preprocessor.process_intertie:
        if preprocessor.intertie_status == 'child':
            ids = [preprocessor.communities[1],preprocessor.aliases[1]]
        else:
            ids = [preprocessor.communities[0],preprocessor.aliases[0]]
    else:
       ids = [preprocessor.communities[0],preprocessor.aliases[0]]
    
    data = data.ix[ids][data.ix[ids].isnull().all(1) == False]
    
    try:
        max_savings = float(data['Maximum savings ($/kWh)'])
        nearest_comm = data['Nearest Community with Lower Price Power']
        nearest_comm = str(nearest_comm.values[0])
        if 'nan' == nearest_comm:
            nearest_comm = ''
        distance = float(data['Distance to Community'])
    except TypeError:
        max_savings = np.nan
        nearest_comm = ''
        distance = np.nan
        
    yto = 5 # years tp operation
    start_year = preprocessor.data['community']['current year'] + yto
    
    return  {
        "Transmission and Interties" : {
            'enabled': True,
            'lifetime': 20,
            'start year': start_year,
            
            'transmission loss per mile': .001 * 100,
            'nearest community with lower price': nearest_comm,
            'distance to community': distance,
            'maximum savings': max_savings,

            'percent o&m': 5,
            'heat recovery o&m' : 1500,
            'est. intertie cost per mile': {
                'road needed': 500000, 
                'road not needed': 250000
            },
            'diesel generator o&m': { # upper kW limit: price 
                '150': 84181.00,
                '360': 113410.00, 
                '600': 134434.00, 
                'else': 103851.00 
            }
        }
    }


    
## list of wind preprocessing functions
preprocess_funcs = [preprocess]



