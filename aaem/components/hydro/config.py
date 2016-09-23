"""
config.py

    Hydropower config info for community data yaml file
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
