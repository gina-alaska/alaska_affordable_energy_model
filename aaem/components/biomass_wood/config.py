"""
Biomass Pellet configuration 
----------------------------
    
    Contains biomass pellet configuration info for 
    community data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        hours of storage for peak :
        
        percent at max output :
        
        cordwood system efficiency :
        
        hours operation per cord :
        
        operation cost per hour :
        
        energy density :
        
        boiler assumed output :
        
        cost per btu/hr :
"""
import aaem.components.biomass_base as bmb
from copy import deepcopy

COMPONENT_NAME = "Biomass for Heat (Cordwood)"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = deepcopy(bmb.order) 
order += [
    "hours of storage for peak",
    "percent at max output",
    "cordwood system efficiency",
    "hours operation per cord",
    "operation cost per hour",
    "boiler assumed output"
]

## List of yaml key/value pairs
structure = deepcopy(bmb.structure)
structure[COMPONENT_NAME] = structure.pop(bmb.COMPONENT_NAME)
structure[COMPONENT_NAME].update(    
    {
        "hours of storage for peak" : float,
        "percent at max output" : float,
        "cordwood system efficiency": float,
        "hours operation per cord": float,
        "operation cost per hour": float,
        "boiler assumed output": float
    }
)




## comments for the yaml key/value pairs
comments = deepcopy(bmb.comments)
comments.update(    
    {
        "hours of storage for peak" : '[float]',
        "percent at max output" : '[float]',
        "cordwood system efficiency": '[float]',
        "hours operation per cord": '[float]',
        "operation cost per hour": '[float]',
        "boiler assumed output": '[float]'
    }
) 

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)
