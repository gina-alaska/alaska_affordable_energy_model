"""
Water Wastewater Configuration
------------------------------

    Contains Water Wastewater configuration info for community
    data yaml file, and other set-up requirements

"""
from aaem.components import definitions

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
    'enabled': definitions.ENABLED,
    'lifetime': definitions.LIFETIME,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'audit cost': '[float] price [$]',
    'average refit cost': '[float] Statewide average cost per person for refitting water and wastewater facilities [$],
    'data': '[dict] Data',
    'electricity refit reduction':
        '[float] percent saved by performing electricity refit [%]',
    'heating fuel refit reduction':
         '[float] percent saved by performing heating fuel refit [%]',
    'heat recovery multiplier': '[float] multiplier for assumed baseline heat fuel consumption if heat recovery is used in the community'
    }

## list of prerequisites for module
prereq_comps = []

## List of raw data files required for  preprocessing
raw_data_files = []
