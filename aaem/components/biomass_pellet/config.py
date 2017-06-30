"""
Biomass Pellet configuration
----------------------------

    Contains biomass pellet configuration info for
    community data yaml file, and other set-up requirements

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
        "pellet efficiency": '[float] efficiency of pellet boiler',
        "default pellet price": '[float] default price for pellets [$/ton]'
    }
)

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)
