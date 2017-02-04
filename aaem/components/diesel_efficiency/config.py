"""
Diesel Efficiency Configuration 
-------------------------------
    
    Contains configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'efficiency improvments' : 
        
        'o&m costs': operation and maintainence cost per yer
    
    
"""
COMPONENT_NAME = "Diesel Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": {'phase': 'Reconnaissance',
                            'capital costs': UNKNOWN,
                            'operational costs': UNKNOWN,
                            'expected years to operation': 3,
                            },
        'data': IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'efficiency improvment': 1.1,
        'o&m costs': {150: 84181.00,
                      360: 113410.00,
                      600: 134434.00,
                      'else':103851.00 }
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


## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []

## list of prerequisites for module
prereq_comps = [] ## FILL in if needed

DESCRIPTION = """
    This component calculates the potential electricity generation from diesel offset by improving diesel efficiency in a community.
"""

