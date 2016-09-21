"""
config.py

    Biomass - Pellet config info for community data yaml file
"""
import aaem.components.biomass_base as bmb
from copy import deepcopy

COMPONENT_NAME = "biomass pellet"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = deepcopy(bmb.yaml)
yaml["energy density"] = 17600000
yaml["pellet efficiency"] = .8
yaml["cost per btu/hr"] = .54
yaml["default pellet price"] = 400


## default values for yaml key/Value pairs
yaml_defaults = deepcopy(bmb.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(bmb.yaml_order) + ["pellet efficiency",
                                "cost per btu/hr",
                                "default pellet price"]

## comments for the yaml key/value pairs
yaml_comments = deepcopy(bmb.yaml_comments)
yaml_comments["energy density"] = "energy density of pellets (btu/ton) <float>"
yaml_comments["pellet efficiency"] = \
                        "effcicieny of pellets (% as decimal) <float>"
yaml_comments["cost per btu/hr"] = "cost per btu/hr ($) <float>"
yaml_comments["default pellet price"] = "pellet cost per ton ($) <float>" 

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)
