"""
Diesel Efficiency preprocessing 
-------------------------------

preprocessing functions for Diesel Efficiency component  

"""
## List of raw data files required for wind power preproecssing 
raw_data_files = ['project_development_timeframes.csv']

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
    start_year = preprocessor.data['community']['current year'] + 3
    
    return {
        'Diesel Efficiency' : {
            'enabled': True,
            'lifetime': 20, 
            'start year': start_year,
            'efficiency improvment': 10,
            'o&m costs': {
                '360': 113410.0,
                '600': 134434.0,
                '150': 84181.0,
                'else': 103851.0,
            }
        }
    }

