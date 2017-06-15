"""
Diesel Efficiency Configuration 
-------------------------------
    
    Contains configuration info for community data yaml file, and 
     other set-up requirements
    
    **Unique Configuration keys**
    
        'efficiency improvments' : 
        
        'o&m costs': operation and maintainence cost per yer
    
    
"""
COMPONENT_NAME = "Diesel Efficiency"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = [
    'enabled',
    'lifetime', 
    'start year',
    'efficiency improvment',
    'o&m costs'
]

structure = {
    'Diesel Efficiency' : {
        'enabled': bool,
        'lifetime': int, 
        'start year': int,
        'efficiency improvment': float,
        'o&m costs': dict
    }
}

comments = {
    'enabled': '[bool]',
    'lifetime': '[int]', 
    'start year': '[int]',
    'efficiency improvment': '[float]',
    'o&m costs': '[dict]'

}




## list of prerequisites for module
prereq_comps = [] ## FILL in if needed

