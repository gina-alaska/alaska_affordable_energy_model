"""
Biomass Base Configuration 
--------------------------
    
    Contains Biomass Base configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        energy density: energy density of  fuel
        
        data: data on biomass related items
        
"""
from aaem.components import definitions

COMPONENT_NAME = "biomass base"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime',
    'start year',
    
    'cost per btu/hrs',
    'o&m per year',
    
    'sufficient biomass',
    'peak month % of total',
    'capacity factor',
    'energy density',
]

structure = {
    COMPONENT_NAME: {
        'enabled': bool, # 
        'lifetime': int, # number years <int>
        'start year': int, # start year <int>
        
        'cost per btu/hrs': float,
        'o&m per year': float,
        
        'sufficient biomass': 
            bool,
        'peak month % of total':float,
        'capacity factor': float,
        
        'energy density': float,
        
    }
}

comments = {
    'enabled': definitions.ENABLED, # 
    'lifetime': definitions.START_YEAR_WITH_TYPE, # number years <int>
    'start year': definitions.LIFETIME, # start year <int>
    
    'cost per btu/hrs': '[float] cost per btu/hrs',
    'o&m per year': '[float] operation and maintenence cost per year [$/year]',
    
    'sufficient biomass': '[bool] indicates if there is sufficient biomass to heat community',
    'peak month % of total': '[float] percent of yearly energy output for month with highest consumption',
    'capacity factor': '[float] ',
    
    'energy density': '[float] energy density of biomass fuel',
}
                
## list of prerequisites for module
prereq_comps = ["Non-residential Energy Efficiency",]
