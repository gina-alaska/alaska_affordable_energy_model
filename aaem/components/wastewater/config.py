"""
config.py

    Water/Waste Water efficiency config info for community data yaml file
"""
COMPONENT_NAME = 'Water and Wastewater Efficiency'
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'audit cost': 10000,
        'average refit cost': 360.00,
        'data': 'IMPORT',
        'electricity refit reduction': .25,
        'heating fuel refit reduction': .35,
        'heat recovery multiplier': {True: .5, False: 1.0}
            }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 15,
        'start year': 2017,
        }

## order to save yaml
yaml_order = ['enabled','lifetime','start year','audit cost',
             'average refit cost', 'data', 'electricity refit reduction',
             'heating fuel refit reduction', 'heat recovery multiplier']

## comments for the yaml key/value pairs
yaml_comments = {
    'enabled':'',
    'lifetime': 'number years <int>',
    'start year': 'start year <int>',
    'audit cost': 'price <float> (ex. 10000)',
    'average refit cost': 'cost/per person <float>',
    'data': '',
    'electricity refit reduction': 
        'decimal precent <float> percent saved by preforming electricity refit',
    'heating fuel refit reduction': 
        'decimal precent <float> percent saved by heating fuel refit',
    'heat recovery multiplier': ''
    }
    
## list of prerequisites for module
prereq_comps = []

## List of raw data files required for  preproecssing 
raw_data_files = []

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []

