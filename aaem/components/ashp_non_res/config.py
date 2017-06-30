"""
Air Source Heat Pump Non-residential Configuration
-------------------------------------------------

    Contains Air Source Heat Pump Non-residential configuration info for
    community data yaml file, and other set-up requirements

"""
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

COMPONENT_NAME = "Non-Residential ASHP"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

order = deepcopy(ashp_base.order)

## List of yaml key/value pairs
structure = deepcopy(ashp_base.structure)
structure[COMPONENT_NAME] = structure.pop(ashp_base.COMPONENT_NAME)

## comments for the yaml key/value pairs
comments = deepcopy(ashp_base.comments)

prereq_comps = ['Non-residential Energy Efficiency']
