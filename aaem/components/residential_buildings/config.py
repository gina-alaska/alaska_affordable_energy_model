"""
Residential Efficiency configuration 
------------------------------------
    
    Contains configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'min kWh per household'
        'average refit cost'
        'data'
    
"""
COMPONENT_NAME = "Residential Energy Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled', 
    'start year',
    'lifetime', 
    'min kWh per household', 
    'average refit cost',
    'data'
]

structure = {
    'Residential Energy Efficiency':{
        'enabled':bool, 
        'start year':int,
        'lifetime': int, 
        'min kWh per household': float, 
        'average refit cost': float,
        'data': dict
    }
}

comments = {
    'enabled': 'bool', 
    'start year': 'int',
    'lifetime': 'int', 
    'min kWh per household': 'float', 
    'average refit cost': 'float',
    'data': 'dict'

}



## list of prerequisites for module
prereq_comps = []
