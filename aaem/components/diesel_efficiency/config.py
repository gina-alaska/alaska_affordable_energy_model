"""
Diesel Efficiency Configuration
-------------------------------

    Contains configuration info for community data yaml file, and
     other set-up requirements

"""
from aaem.components import definitions

COMPONENT_NAME = "Diesel Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    'efficiency improvement',
    'o&m costs'
]

structure = {
    'Diesel Efficiency' : {
        'enabled': bool,
        'lifetime': int,
        'start year': int,
        'efficiency improvement': float,
        'o&m costs': dict
    }
}

comments = {
    'enabled': definitions.ENABLED,
    'lifetime': definitions.LIFETIME,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'efficiency improvement': '[float] percent efficiency improvement [%]',
    'o&m costs': '[dict] costs(values) for upper limit kW capacities(keys) with a key else for other values'

}

## list of prerequisites for module
prereq_comps = [] ## FILL in if needed
