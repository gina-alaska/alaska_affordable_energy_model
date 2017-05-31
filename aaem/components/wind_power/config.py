"""
Wind Power Configuration 
------------------------
    
    Contains Transmission configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        'default distance to resource'
        'average load limit'
        'percent generation to offset'
        'resource data'
        'secondary load'
        'secondary load cost'
        'road needed for transmission line'
        'est. transmission line cost'
        'costs'
        'percent o&m'
        'percent heat recovered'
    
"""
from pandas import DataFrame
from aaem.components import definitions

COMPONENT_NAME = "Wind Power"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    'average load limit',
    'percent generation to offset',
    
    'phase',
    'proposed capacity',
    'generation capital cost',
    'operational costs',
    'proposed generation',
    'distance to resource',
    'transmission capital cost',
    
    'wind class',
    'capacity factor',
    'percent heat recovered',
    'secondary load',
    
    
    'secondary load cost',
    'percent o&m',
    'estimated costs',
    'est. transmission line cost'
]

structure = {
    'Wind Power': {
        'enabled': bool,
        'lifetime': int, 
        'start year': int,
        'average load limit': float,
        'percent generation to offset': float,
        
        'phase': str,
        'proposed capacity': [float, str],
        'generation capital cost': [float, str],
        'operational costs': [float, str],
        'proposed generation': [float, str],
        'distance to resource': float, 
        'transmission capital cost': [float, str],
        
        
        'wind class': float,
        'capacity factor': float,
        'percent heat recovered': float,
        'secondary load': bool,
        
        
        'secondary load cost': float, # 
        'percent o&m': float,
        'estimated costs': DataFrame,
        'est. transmission line cost': float,
    }
}

comments = {
    'enabled': 'bool',
    'lifetime': 'int', 
    'start year': 'int',
    'average load limit': 'float',
    'percent generation to offset': 'float',
    
    'phase': 'str',
    'proposed capacity': 'f[float, str]',
    'generation capital cost': 'f[float, str]',
    'operational costs': 'f[float, str]',
    'proposed generation': 'f[float, str]',
    'distance to resource': 'float', 
    'transmission capital cost': 'f[float, str]',
    
    
    'wind class': 'float',
    'capacity factor': 'float',
    'percent heat recovered': 'float',
    'secondary load': 'bool',
    
    
    'secondary load cost': 'float', # 
    'percent o&m': 'float',
    'estimated costs': 'DataFrame',
    'est. transmission line cost': 'float',
}

## list of prerequisites for module
prereq_comps = []

