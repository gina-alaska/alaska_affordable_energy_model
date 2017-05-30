"""
Hydropower configuration 
------------------------
    
    Contains configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'percent heat recovered' : percent heat recovered
        
        'percent o&m': percent of captial costs for o&m
    
    
"""
COMPONENT_NAME = "Hydropower"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"


order = [
    'enabled',
    'lifetime',
    'start year',

    'name',
    'phase',
    'proposed capacity',
    'proposed generation',
    'generation capital cost',
    'transmission capital cost',
    #~ 'expected years to operation',
    'source',

    'percent o&m',
    'percent heat recovered',
    
]

structure = {
    'Hydropower': {
        'enabled': bool, 
        'start year': int,
        'lifetime': int, 
        
        'name': [unicode, str],
        'phase': str,
        'proposed capacity': [str, float],
        'proposed generation': [str, float],
        'generation capital cost': [str, float],
        'transmission capital cost': [str, float],
        #~ 'expected years to operation': [str, int],
        'source': str,
        
        'percent o&m': float,
        'percent heat recovered': float,
    }
}

comments = {
    'enabled': '', 
    'start year': '',
    'lifetime': '', 
    'project details': '',
    
    'name': '',
    'phase': '',
    'proposed capacity': '',
    'proposed generation': '',
    'generation capital cost': '',
    'transmission capital cost': '',
    #~ 'expected years to operation': '',
    'source': '',
    
    'percent o&m': '',
    'percent heat recovered': '',
}



        

## list of prerequisites for module
prereq_comps = []
