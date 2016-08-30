"""
config.py

    Biomass - Base config info for community data yaml file
"""
COMPONENT_NAME = "biomass base"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'heating oil efficiency': .75,
        'energy density': 'ABSOLUTE DEFAULT',
        'data': 'IMPORT',
        'percent sqft assumed heat displacement': .3,
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year','heating oil efficiency',
               'energy density', 'data']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'heating oil efficiency': '% as decimal <float>',
        'energy density': 'BTU/fuel unit (specified in child) <float>',
        'data': 'biomass data'}
        
## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []

## list of prerequisites for module
prereq_comps = ["non-residential buildings",]
