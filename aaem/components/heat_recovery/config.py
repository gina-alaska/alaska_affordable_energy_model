"""
Heat Recovery Configuration
---------------------------

    Contains heat recovery configuration info for community data yaml file, and
      other set-up requirements

"""
from aaem.components import definitions

COMPONENT_NAME = "Heat Recovery"
PROJECT_TYPE = 'heat_recovery'
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    'est. current annual heating fuel gallons displaced',
    'estimate pipe distance',
    'estimate pipe cost/ft',
    'estimate buildings to heat',
    'heating conversion efficiency',
    'percent heat recovered',
    'estimate cost/building',
    'o&m per year',
    'name',
    'phase',
    'project type',
    'identified as priority',
    'capital costs',
    'number buildings',
    'buildings',
    'total feet piping needed',
    'proposed maximum btu/hr',
    'proposed gallons diesel offset',
    'link',
    'notes',
]

structure = {
    'Heat Recovery' : {
        'enabled': bool,
        'lifetime': int,
        'start year': int,
        'est. current annual heating fuel gallons displaced': [float, str],
        'estimate pipe distance': float,
        'estimate pipe cost/ft': float,
        'estimate buildings to heat': int,
        'heating conversion efficiency': float,
        'percent heat recovered': float,
        'estimate cost/building': float,
        'o&m per year': float,
        'name': str,
        'phase': str,
        'project type': str,
        'capital costs': [float, str],
        'number buildings': [int, str],
        'buildings': list,
        'total feet piping needed': [float, str],
        'proposed maximum btu/hr':[float, str],
        'proposed gallons diesel offset': [float, str],
        'link': str,
        'notes': str,
        'identified as priority': str

    }
}

comments = {
    'enabled': definitions.ENABLED,
    'lifetime': definitions.LIFETIME,
    'start year': definitions.START_YEAR_WITH_TYPE,
    'est. current annual heating fuel gallons displaced': '[float, str]',
    'estimate pipe distance':
        '[float] estimated pipe distance in feet if "total feet piping needed" is unknown [ft]',
    'estimate pipe cost/ft': '[float] estimated cost per foot of piping needed [$/ft]',
    'estimate buildings to heat': '[int] estimated number of buildings if "number buildings" is unknown',
    'heating conversion efficiency': '[float] efficiency of heat recovery',
    'percent heat recovered': '[float] percent of heat recoverable [%]',
    'estimate cost/building': '[float] estimate cost per building [$/building]',
    'o&m per year': '[float] operation and maintenance cost per year [$/year]' ,
    'name': definitions.NAME,
    'buildings': '[list] list of buildings',
    'phase': definitions.PHASE_WITH_TYPE,
    'project type': '[str] project type: New/Repair/Extension',
    'capital costs': '[float] capital costs for project [$]',
    'number buildings': '[float] known number of buildings',
    'total feet piping needed': '[float] total feet of piping required [ft]',
    'proposed maximum btu/hr': '[float] proposed maximum output of boiler [btu/hr]',
    'proposed gallons diesel offset': '[float] proposed gallons of diesel to offset [gallons]',
    'link': '[str]',
    'notes': definitions.NOTES,
    'identified as priority': '[str] is project identified as priority (yes/no)',
}

## list of prerequisites for module
prereq_comps = []
