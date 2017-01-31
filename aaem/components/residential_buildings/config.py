"""
config.py

    Residential Building Efficiency config info for community data yaml file
"""
COMPONENT_NAME = "Residential Energy Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

yaml = {'enabled': False,
        'min kWh per household': 6000,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'average refit cost': 11000,
        'data': 'IMPORT'}
        
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2017,
        }
        
yaml_order = ['enabled', 'min kWh per household', 'lifetime', 'start year',
              'average refit cost', 'data']

yaml_comments = {'enabled': '',
        'min kWh per household': 
                'minimum average consumed kWh/year per house<int>',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average refit cost': 'cost/refit <float>',
        'data': 'IMPORT'}

## list of prerequisites for module
prereq_comps = []

DESCRIPTION = """
    This component calculates the potential reduction heating oil by improving the efficiency residential buildings
"""
