"""
Non-residential Efficiency configuration 
----------------------------------------
    
    Contains configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'average refit cost' 
        'cohort savings multiplier'
        'com building data'
        'number buildings'
        'com building estimates'
        'heating cost precent'
        'HW District price %'
    
"""
COMPONENT_NAME = "Non-residential Energy Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

yaml = {'enabled': False,
        'lifetime': 'ABSOLUTE DEFAULT',
        'start year': 'ABSOLUTE DEFAULT',
        'average refit cost': 7.00,
        'cohort savings multiplier': .26,
        'com building data': 'IMPORT',
        'number buildings': 'IMPORT',
        'com building estimates': 'IMPORT',
        'heating cost precent': .6,
        'HW District price %': .5,
            }
            
yaml_defaults = {'enabled': True,
        'lifetime': 15,
        'start year': 2017,
        }
            
yaml_order = {'enabled','lifetime','start year','average refit cost',
                 'cohort savings multiplier','com building data',
                 'number buildings', 'com building estimates'
            }

yaml_comments = {'enabled': '',
                'lifetime': 'number years <int>',
                'start year': 'start year <int>',
                'average refit cost': 'cost/sqft. <float>',
                'cohort savings multiplier': 'pecent as decimal <float>',
                'com building data': '',
                'number buildings': '',
                'com building estimates': '',
                'heating cost precent': 
                    ('% of total capital costs used for thermal efficiency'
                        ' pecent as decimal <float>'),
                'HW District price %': 
                    ('the percent of the heaing oil price that is'
                                                ' the HW District price'),
            }
            
## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []          

## list of prerequisites for module
prereq_comps = []

