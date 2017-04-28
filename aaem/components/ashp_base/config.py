"""
Air Sorce Heat Pump Base Configuration 
--------------------------------------
    
    Contains Air Sorce Heat Pump Base configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        perfromance data: data on ASHP prefromance in community
        
        data: general data on stsyem
        
        o&m per year: cost of maintainence
        
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
