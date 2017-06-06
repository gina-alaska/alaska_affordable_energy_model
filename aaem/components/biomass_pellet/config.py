"""
Biomass Pellet configuration 
----------------------------
    
    Contains biomass pellet configuration info for 
    community data yaml file, and other set-up requirements
    
    **Unique Configuration keys**
    
        energy density: energy density of biomass fuel (btu/ton)
        
        pellete efficiency: effcicieny of pellets (% as decimal)

        cost per btu/hr: cost per btu/hr ($)
        
        default pellete price: pellet cost per ton ($)
"""
import aaem.components.biomass_base as bmb
from copy import deepcopy

COMPONENT_NAME = "Biomass for Heat (Pellet)"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"


order = deepcopy(bmb.order) 
order += [
    "pellet efficiency",
    "default pellet price"
]

## List of yaml key/value pairs
structure = deepcopy(bmb.structure)
structure[COMPONENT_NAME] = structure.pop(bmb.COMPONENT_NAME)
structure[COMPONENT_NAME].update(    
    {
        "pellet efficiency": float,
        "default pellet price": float
    }
)




## comments for the yaml key/value pairs
comments = deepcopy(bmb.comments)
comments.update(    
    {
        "pellet efficiency": '[float]',
        "default pellet price": '[float]'
    }
) 

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)


