"""
Wind Power Configuration
------------------------

    Contains Transmission configuration info for community
    data yaml file, and other set-up requirements

"""
from pandas import DataFrame
from aaem.components import definitions

COMPONENT_NAME = "Wind Power"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    'average load limit',
    'percent generation to offset',


    'name',
    'source',
    'notes',
    'phase',
    'proposed capacity',
    'generation capital cost',
    'operational costs',
    'proposed generation',
    'distance to resource',
    'transmission capital cost',

    'wind class',
    'capacity factor',
    'percent heat recovered',
    'secondary load',


    'secondary load cost',
    'percent o&m',
    'estimated costs',
    'est. transmission line cost'
]

structure = {
    'Wind Power': {
        'enabled': bool,
        'lifetime': int,
        'start year': int,
        'average load limit': float,
        'percent generation to offset': float,

        'name': str,
        'source': str,
        'notes': str,
        'phase': str,
        'proposed capacity': [float, str],
        'generation capital cost': [float, str],
        'operational costs': [float, str],
        'proposed generation': [float, str],
        'distance to resource': float,
        'transmission capital cost': [float, str],


        'wind class': float,
        'capacity factor': float,
        'percent heat recovered': float,
        'secondary load': bool,


        'secondary load cost': float, #
        'percent o&m': float,
        'estimated costs': DataFrame,
        'est. transmission line cost': float,
    }
}

comments = {
    'enabled': definitions.ENABLED,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'lifetime': definitions.LIFETIME,
    'average load limit': '[float] Minimum average diesel load required for wind gereration to be cosidered[kW]',
    'percent generation to offset': '[float] Percent of diesel generaton to offset with wind generation.',

    'name': definitions.NAME,
    'source': definitions.SOURCE,
    'notes': definitions.NOTES_WITH_TYPE,
    'phase': definitions.PHASE_WITH_TYPE,
    'proposed capacity': '[float, str] Proposed wind generation capacity form known project [kW], or UNKNOWN',
    'generation capital cost': '[float, str] Capital costs for generation infastructure [$], or UNKNOWN',
    'operational costs': '[float, str] Operational costs for generation infastructure [$], or UNKNOWN',
    'proposed generation': '[float, str] Proposed yearly wind generation from known project [kWh], or UNKNOWN',
    'distance to resource': '[float] Distance to proposed wind infastructure [ft], or UNKNOWN',
    'transmission capital cost': '[float, str] Capital costs for transmission infastructure [$], or UNKNOWN',

    'wind class': '[float] classification system to describe typical wind conditions in community',
    'capacity factor': '[float] unitless ratio of actual electrical energy output to maximum possible output over given time period',
    'percent heat recovered': '[float] Precent heat recoverable in wind generation systems',
    'secondary load': '[bool] secondary load available',


    'secondary load cost': '[float] cost for secondary load [$]', #
    'percent o&m': '[float] percent of capital costs to use as yearly operational costs if operational costs are UNKNOWN',
    'estimated costs': '[DataFrame] Table estimated cost for generation infastructure [$] at different capacities [kW] if generation costs are UNKNOWN',
    'est. transmission line cost': '[float] Estimated cost for transmission generation infastructure [$] if transmission costs are UNKNOWN',
}

## list of prerequisites for module
prereq_comps = []
