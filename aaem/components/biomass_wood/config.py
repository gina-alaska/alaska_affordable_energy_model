"""
Biomass Pellet configuration 
----------------------------
    
    Contains biomass pellet configuration info for 
    community data yaml file, and other set-up requirements
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
        "hours of storage for peak" : '[float] ',
        "percent at max output" : '[float] percent of time at max output',
        "cordwood system efficiency": '[float] efficiency cordwood boiler',
        "hours operation per cord": '[float] hours each cord burns for [hours]',
        "operation cost per hour": '[float] cost to operate cordwood boiler [$/hour]',
        "boiler assumed output": '[float] assumed output of boiler [btu/hrs]'
    }
) 

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)
