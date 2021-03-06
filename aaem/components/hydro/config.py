"""
Hydropower configuration
------------------------

    Contains configuration info for community data yaml file, and
     other set-up requirements

"""
from aaem.components import definitions

COMPONENT_NAME = "Hydropower"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"


order = [
    'enabled',
    'lifetime',
    'start year',

    'name',
    'phase',
    'proposed capacity',
    'proposed generation',
    'generation capital cost',
    'transmission capital cost',
    'source',

    'percent o&m',
    'percent heat recovered',

]

structure = {
    'Hydropower': {
        'enabled': bool,
        'start year': int,
        'lifetime': int,

        'name': [unicode, str],
        'phase': str,
        'proposed capacity': [str, float],
        'proposed generation': [str, float],
        'generation capital cost': [str, float],
        'transmission capital cost': [str, float],
        'source': str,

        'percent o&m': float,
        'percent heat recovered': float,
    }
}

comments = {
    'enabled': definitions.ENABLED,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'lifetime': definitions.LIFETIME,
    'name': definitions.NAME,
    'phase': definitions.PHASE_WITH_TYPE,
    'proposed capacity': '[float] proposed generation capacity [kW]',
    'proposed generation': '[float] proposed generation per year [kWh]',
    'generation capital cost':
        '[float] cost of installing generation infrastructure [$]',
    'transmission capital cost':
        '[float] cost of installing any transmission infrastructure [$]',
    'source': '[str] link to source document',
    'percent o&m': '[float] percent of capital costs used for annual o&m costs [%]',
    'percent heat recovered': '[float] percent heat recovery by hydro system [%]',
}

## list of prerequisites for module
prereq_comps = ['Non-residential Energy Efficiency']
