"""
Solar Power Configuration
-------------------------

    Contains solar power configuration info for community
    data yaml file, and other set-up requirements

"""
from aaem.components import definitions

COMPONENT_NAME = "Solar Power"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',

    'average load limit',
    'percent generation to offset',
    'percent solar degradation',

    'output per 10kW solar PV',
    #~ 'road needed',
    #~ 'road needed for transmission line',
    #~ 'transmission line distance',

    'cost',
    'switch gear needed for solar',
    'cost per kW',
    #~ 'o&m cost per kWh',
    'percent o&m',
]

structure = {
    'Solar Power': {
        'enabled': bool,
        'lifetime': int,
        'start year': int ,

        'average load limit' : float,
        'percent generation to offset': float,
        'percent solar degradation': float,

        'output per 10kW solar PV': float,
        #~ 'road needed': bool,
        #~ 'road needed for transmission line': bool,
        #~ 'transmission line distance': float,

        'cost': [float, str],
        'switch gear needed for solar': bool,
        'cost per kW': float,
        #~ 'o&m cost per kWh': float,
        'percent o&m': float,

    }
}

comments = {
    'enabled': definitions.ENABLED,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'lifetime': definitions.LIFETIME,

    'average load limit' :
        ('[float] minimum average diesel load (kW) in community required before'
         ' solar power is considered'),
    'percent generation to offset': '[float] percent of diesel load to offset',
    'percent solar degradation':
        '[float] annual decline in solar effectiveness',

    'output per 10kW solar PV': '[float] output from solar panel',
    #~ 'road needed': '[bool]',
    #~ 'road needed for transmission line': '[bool]',
    #~ 'transmission line distance': '[float] distance of road needed  in miles',

    'cost': '[float] cost or [str] UNKNOWN',
    'switch gear needed for solar': '[bool]',
    'cost per kW': '[float] cost per kW if cost of the project is UNKNOWN',
    #~ 'o&m cost per kWh': '[float] cost of repairs for diesel generator per kWh',
    'percent o&m':
        '[float] yearly maintenance cost as percent as decimal of total cost',
}


## list of prerequisites for module
prereq_comps = []
