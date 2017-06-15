"""
Biomass Base Configuration 
--------------------------
    
    Contains Biomass Base configuration info for community
    data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        energy density: energy density of  fuel
        
        data: data on biomass related items
        
"""
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
    'enabled': '[bool]', # 
    'lifetime': '[int]', # number years <int>
    'start year': '[int]', # start year <int>
    
    'cost per btu/hrs': '[float]',
    'o&m per year': '[float]',
    
    'sufficient biomass': 
        '[bool]',
    'peak month % of total': '[float]',
    'capacity factor': '[float]',
    
    'energy density': '[float]',
}
                
## list of prerequisites for module
prereq_comps = ["Non-residential Energy Efficiency",]
