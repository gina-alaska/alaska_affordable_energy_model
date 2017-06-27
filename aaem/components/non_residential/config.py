"""
Non-residential Efficiency configuration
----------------------------------------

    Contains configuration info for community data yaml file, and
     other set-up requirements

"""
from pandas import DataFrame
from aaem.components import definitions

COMPONENT_NAME = "Non-residential Energy Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'start year',
    'lifetime',
    'average refit cost',
    'cohort savings percent',
    'heating percent',
    'waste oil cost percent',
    'number buildings',
    'consumption estimates',
    'building inventory'
]

structure = {
    'Non-residential Energy Efficiency':{
        'enabled': bool,
        'start year': int,
        'lifetime': int,
        'average refit cost': float,
        'cohort savings percent': float,
        'heating percent': float,
        'waste oil cost percent': float,
        'number buildings': int,
        'consumption estimates':  DataFrame,
        'building inventory': DataFrame
    }

}

comments = {
        'enabled': definitions.ENABLED,
        'start year': definitions.START_YEAR_WITH_TYPE,
        'lifetime': definitions.LIFETIME,
        'average refit cost':
            ('[float > 0] Average refit cost per square foot ($/sqft) for '
            'non-residential buildings'),
        'cohort savings percent':
            ('[float > 0] Amount of energy saved in a retrofit system'
            ' as a percent'),
        'heating percent': (
            '[float > 0] percent of energy consumption from heating'
            ),
        'waste oil cost percent':
            ('[float > 0] The percentage of the heating oil price that'
            ' should be used as waste oil price'),
        'number buildings':
            ('[int >= 0] number non-residential buildings'
            ' in community'),
        'consumption estimates':
            ('[DataFrame] estimates for consumption and size of '
            'unknown buildings in a community'),
        'building inventory':
            ('[DataFrame] An inventory of known buildings in a community and '
            'their consumption values if known')

}

## list of prerequisites for module
prereq_comps = []
