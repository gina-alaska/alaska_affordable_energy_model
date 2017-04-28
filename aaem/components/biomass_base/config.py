"""
Biomass Base Configuration 
--------------------------
    
    Contains Biomass Base configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        energy density: energy density of  fuel
        
        data: data on biomass related items
        
"""
COMPONENT_NAME = "biomass base"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'energy density': 'ABSOLUTE DEFAULT',
        'data': 'IMPORT',
        }

## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2017,
        }
    
## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year',
               'energy density', 'data']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'energy density': 'BTU/fuel unit (specified in child) <float>',
        'data': 'biomass data'}

## list of prerequisites for module
prereq_comps = ["Non-residential Energy Efficiency",]
