"""
Residential Efficiency configuration
------------------------------------

    Contains configuration info for community data yaml file, and
     other set-up requirements

"""
from aaem.components import definitions

COMPONENT_NAME = "Residential Energy Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'start year',
    'lifetime',
    'min kWh per household',
    'average refit cost',
    'data'
]

structure = {
    'Residential Energy Efficiency':{
        'enabled':bool,
        'start year':int,
        'lifetime': int,
        'min kWh per household': float,
        'average refit cost': float,
        'data': dict
    }
}

comments = {
    'enabled': definitions.ENABLED,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'lifetime': definitions.LIFETIME,
    'min kWh per household': '[float] Minimum electricity consumption per household [kWh]',
    'average refit cost': '[float] Statewide average cost for refitting household to meet energy efficiency standards [$]',
    'data': '[dict] Residential consumption data'
}

## list of prerequisites for module
prereq_comps = []
