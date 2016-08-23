"""
config.py

    Air Source Heat Pumps Base config info for community data yaml file
"""
COMPONENT_NAME = "air source heat pumps base"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'perfromance data': 'IMPORT',
        'data':'IMPORT',
        'heating oil efficiency': .75,
        'o&m per year': 320
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 15,
        'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>'}

## list of prerequisites for module
prereq_comps = []

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = ['perfromance data','data']
    


