"""
Transmission Configuration 
--------------------------
    
    Contains Transmission configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        'transmission loss per mile'
        'nearest community'
        'heat recovery o&m' 
        'est. intertie cost per mile'
        'percent o&m'
        'diesel generator o&m'
    
"""
COMPONENT_NAME = "Transmission and Interties"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'transmission loss per mile': .001,
        'nearest community': IMPORT,
        'heat recovery o&m' : 1500,
        'est. intertie cost per mile': {'road needed': 500000, 
                                        'road not needed': 250000},
        'percent o&m':.05,
        'diesel generator o&m': {'150': 84181.00,
                   '360': 113410.00, 
                   '600': 134434.00, 
                   'else': 103851.00 }
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        #~ 'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>'}
        
    
## list of prerequisites for module
prereq_comps = [] 
