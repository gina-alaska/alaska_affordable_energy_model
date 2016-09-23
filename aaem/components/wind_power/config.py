"""
config.py

    Wind Power config info for community data yaml file
"""
COMPONENT_NAME = "Wind Power"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = {'enabled': False,

        "project details": IMPORT,#{
        
            #~ 'phase':IMPORT,
            #~ 'proposed capacity': IMPORT,
            #~ 'proposed generation': IMPORT,
            #~ 'distance to resource': IMPORT,
            #~ 'generation capital cost':IMPORT,
            #~ 'transmission capital cost': IMPORT,
            #~ 'operational costs': IMPORT,
            #~ 'expected years to operation':IMPORT,
                #~ },
        
        'default distance to resource': 1,

        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        
        'average load limit': 100.0,
        'percent generation to offset': 1.00,
        'resource data':'IMPORT',
         #'minimum wind class': 3,
        #~ 'generation capital cost': 'UNKNOWN', #  same as generation captial cost
        'secondary load': True,
        'secondary load cost': 200000,
        'road needed for transmission line' : True,
        'est. transmission line cost': { True:500000, False:250000},
        'costs': 'IMPORT',
        'percent o&m': .01,
        'percent heat recovered': .15,
        }
      
## default values for yaml key/Value pairs
yaml_defaults = {'enabled': True,
        'lifetime': 20,
        'start year': 2020,
        }

## order to save yaml
yaml_order = ['enabled', 'lifetime', 'start year']

## comments for the yaml key/value pairs
yaml_comments = {'enabled': '',
        'lifetime': 'number years <int>',
        'start year': 'start year <int>',
        'average load limit': 
                'lower limit in kW on average load required to do project',
        'percent generation to offset': '',
        'minimum wind class': 'minimum wind class for feasibility',
        'secondary load': '',
        'secondary load cost': '',
        'road needed for transmission line':'',
        'distance to resource': 'miles defaults to 1 mile',
        'est. transmission line cost': 'cost/mile',
        'assumed capacity factor': "TODO read in preprocessor",
        'percent heat recovered': '% as decimal <float>',
        }
        
## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = ['costs']

## list of prerequisites for module
prereq_comps = []
