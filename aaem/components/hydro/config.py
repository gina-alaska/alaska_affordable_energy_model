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

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',

        'percent o&m': .01,
        'percent heat recovered': .15,
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 50,
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
prereq_comps = []

DESCRIPTION = """
    This component calculates the potential electricity generation from diesel offset by installing new hydropower generation infrastructure. This component only uses existing proposed projects to base its calculations on, and does not attempt to model values
"""
