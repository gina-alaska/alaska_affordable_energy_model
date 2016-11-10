"""
config.py

    Solar Power config info for community data yaml file
"""
COMPONENT_NAME = "Solar Power"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'average load limit': 50.0,
        'data': 'IMPORT',
        'cost': 'UNKNOWN',
        'cost per kW': 8000,
        'road needed': False,
        'road needed for transmission line' : True,
        'transmission line distance': 0,
        'percent o&m': .01,
        'percent generation to offset': .15,
        'switch gear needed for solar': False,
        'percent solar degradation': .992,
        'o&m cost per kWh': .02,
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2020,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '<boolean>',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average load limit': 'lower limit on the average load <float>',
        'data': 'data for component',
        'cost': 
            'cost in $ for project if known otherwise UNKNOWN <float|string>',
        'cost per kW': 
            'dollar cost per kW if cost of the project is UNKNOWN <float>',
        'road needed for transmission line' : '<boolean>',
        'transmission line distance': 
            'distance in miles of proposed transmission line <float>',
        'percent o&m': 
            ('yearly maintenance cost'
             ' as percent as decimal of total cost <float>'),
        'percent generation to offset': 
            'pecent of the generation in kW to offset with Solar Power <float>',
        'percent solar degradation': 
            ('the precent of the of solar panel'
             ' that carries over from the previous year'),
        'o&m cost per kWh': 'cost of repairs for generator per kWh <float>',
         }

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = ["data"]

## list of prerequisites for module
prereq_comps = []

DESCRIPTION = """
    This component calculates the potential electricity generation from diesel that could be offset by installing new solar panel infrastructure. 
"""
