"""
Heat Recovery Configuration 
---------------------------
    
    Contains Heat Recovery configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'estimate data': data from heat recovery projects, loaded from data 
        
        'estimate pipe distance': distance of pipe (ft)
        
        'estimate pipe cost/ft': Cost of pipe($/ft)
        
        'estimate buildings to heat': # of buildings estimated to retrofit (#)
        
        'estimate cost/building': estimated cost to retrofit each building ($)
        
        'heating conversion efficiency': efficiency for heat conversion
        
        'o&m per year': operation and maintainence cost per yer
        
        'percent heat recovered': percent of heat recoverd
    
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
        
        'heating conversion efficiency': .75,
        
        'o&m per year': 500,
        'percent heat recovered': .10,
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


DESCRIPTION = """
    This component calculates the potential heating oil offset by installing a new heat recovery System. Requires a known project exists to be run.
"""
