"""
Air Sorce Heat Pump Base Configuration 
--------------------------------------
    
    Contains Air Sorce Heat Pump Base configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        perfromance data: data on ASHP prefromance in community
        
        data: general data on stsyem
        
        o&m per year: cost of maintainence
        
"""
from aaem.components import definitions
    
from pandas import DataFrame

COMPONENT_NAME = "air source heat pumps base"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    'btu/hrs',
    'cost per btu/hrs',
    'o&m per year',
    'data',
    'perfromance data'
]

structure = {
    COMPONENT_NAME: {
        'enabled': bool, # 
        'lifetime': int, # number years <int>
        'start year': int, # start year <int>
        'btu/hrs': float,
        'cost per btu/hrs': float,
        'o&m per year': float,
        
        'data': DataFrame,
        'perfromance data': {
            'COP': list,
            'Temperature': list,
            'Percent of Total Capacity': list,
       } 
    }
}


comments = {
    'enabled': definitions.ENABLED,  
    'lifetime': definitions.LIFETIME,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'btu/hrs': '[float]',
    'cost per btu/hrs': '[float]',
    'o&m per year':'[float]',
    
    'data': '[DataFrame]',
    'perfromance data': '[dict]'
}

## list of prerequisites for module
prereq_comps = []
