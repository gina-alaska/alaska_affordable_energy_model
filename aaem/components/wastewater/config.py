"""
Water Wastewater Configuration 
------------------------------
    
    Contains Water Wastewater configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        'audit cost'
        'average refit cost'
        'data'
        'electricity refit reduction'
        'heating fuel refit reduction'
        'heat recovery multiplier'
        'heating cost precent'
    
"""
COMPONENT_NAME = 'Water and Wastewater Efficiency'
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    'audit cost',
    'average refit cost',
    'electricity refit reduction',
    'heating fuel refit reduction',
    'heat recovery multiplier',
    'heating cost percent',
    'data'
]

structure = {
    'Water and Wastewater Efficiency': {
        'enabled': bool, 
        'start year': int,
        'lifetime': int, 
        'audit cost': float,
        'average refit cost': float, 
        'electricity refit reduction': float,
        'heating fuel refit reduction': float,
        'heat recovery multiplier': float, 
        'heating cost percent': float,
        'data': dict
    }
}


## comments for the yaml key/value pairs
comments = {
    'enabled':'',
    'lifetime': 'number years <int>',
    'start year': 'start year <int>',
    'audit cost': 'price <float> (ex. 10000)',
    'average refit cost': 'cost/per person <float>',
    'data': '',
    'electricity refit reduction': 
        'precent <float> percent saved by preforming electricity refit',
    'heating fuel refit reduction': 
         'precent <float> percent saved by heating fuel refit',
    'heat recovery multiplier': ''
    }
    
## list of prerequisites for module
prereq_comps = []

## List of raw data files required for  preproecssing 
raw_data_files = []
