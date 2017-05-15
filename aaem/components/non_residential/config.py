"""
Non-residential Efficiency configuration 
----------------------------------------
    
    Contains configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'average refit cost' 
        'cohort savings multiplier'
        'com building data'
        'number buildings'
        'com building estimates'
        'heating cost precent'
        'HW District price %'
    
"""
from pandas import DataFrame
COMPONENT_NAME = "Non-residential Energy Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

structure = {
    'Non-residential Energy Efficiency':{
        'enabled': bool,
        'start year': int,
        'lifetime': int,
        'average refit cost': float,
        'cohort savings multiplier': float,
        'heating cost percent': float,
        'waste oil cost percent': float,
        'number buildings': int,
        'consumption estimates':  DataFrame,
        'building inventory': DataFrame
    }

}

comments = {
    'Non-residential Energy Efficiency':{
        'enabled': bool,
        'start year': int,
        'lifetime': int,
        'average refit cost': float,
        'cohort savings multiplier': float,
        'heating cost percent': float,
        'waste oil cost percent': float,
        'number buildings': int,
        'consumption estimates':  DataFrame,
        'building inventory': DataFrame
    }

}

## list of prerequisites for module
prereq_comps = []

