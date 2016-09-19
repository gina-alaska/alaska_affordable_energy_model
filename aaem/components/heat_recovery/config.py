"""
config.py

    Heat Recovery config info for community data yaml file
"""
COMPONENT_NAME = "Heat Recovery"
PROJECT_TYPE = 'heat_recovery'
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        "project details": IMPORT,
        'estimate data': IMPORT,
        'estimate pipe distance': 1500,
        'estimate pipe cost/ft': 135,
        'estimate buildings to heat': 2,
        'estimate cost/building':40000,
        
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'percent heat recovery': .10,
        'heating conversion efficiency': .75,
        
        'o&m per year': 500
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
prereq_comps = []
