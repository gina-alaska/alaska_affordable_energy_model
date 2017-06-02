"""
Heat Recovery Configuration 
---------------------------
    
    Contains Heat Recovery configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'estimate data': data from heat recovery projects, loaded from data 
        
        'estimate pipe distance': distance of pipe (ft)
        
        'estimate pipe cost/ft': Cost of pipe($/ft)
        
        'estimate buildings to heat': # of buildings estimated to retrofit (#)
        
        'estimate cost/building': estimated cost to retrofit each building ($)
        
        'heating conversion efficiency': efficiency for heat conversion
        
        'o&m per year': operation and maintainence cost per yer
        
        'percent heat recovered': percent of heat recoverd
    
"""
from aaem.components import definitions

COMPONENT_NAME = "Heat Recovery"
PROJECT_TYPE = 'heat_recovery'
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime', # number years <int>
    'start year', # start year <int>
    
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
        
        
    }
}

comments = {
    'enabled': definitions.ENABLED,
    'lifetime': definitions.LIFETIME,
    'start year': definitions.START_YEAR_WITH_TYPE,
    
    'estimate pipe distance': 
        ('[float] esitmated pipe distince in feet if'
        ' "total feet piping neede" is unknown'),
    'estimate pipe cost/ft': '[float] estimated cost/foot of piping needed',
    'estimate buildings to heat': 
        ('[int] estimated number of '
        'builings if "number buildings" is unknown'),
    'heating conversion efficiency': '[float]',
    'percent heat recovered': '[float]',
    'estimate cost/building': '[float] $/building',
    'o&m per year': '[float] $' ,
    
    'name': '[str] mame of project',
    'buildings': '[list]',
    'phase': '[str]',
    'project type': '[str] New/Repair/Extension',
    'capital costs': '[float]',
    'number buildings': '[float]',
    'total feet piping needed': '[float]',
    'proposed maximum btu/hr': '[float]',
    'proposed gallons diesel offset': '[float]',
    'link': '[str]',
    'notes': '[str]',

}



## list of prerequisites for module
prereq_comps = []
