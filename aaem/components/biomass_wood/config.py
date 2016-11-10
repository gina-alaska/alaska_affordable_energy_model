"""
config.py

    Biomass - Cordwood config info for community data yaml file
"""
import aaem.components.biomass_base as bmb
from copy import deepcopy

COMPONENT_NAME = "Biomass for Heat (Cordwood)"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = deepcopy(bmb.yaml)
yaml["hours of storage for peak"] = 4
yaml["percent at max output"] = .5
yaml["cordwood system efficiency"] = .88
yaml["hours operation per cord"] = 5.0
yaml["operation cost per hour"] = 20.00
yaml["energy density"] = 16000000
yaml["boiler assumed output"] = 325000
yaml["cost per btu/hr"] = .6

## default values for yaml key/Value pairs
yaml_defaults = deepcopy(bmb.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(bmb.yaml_order) + ["hours of storage for peak",
                               "percent at max output", 
                               "cordwood system efficiency",
                               "hours operation per cord",
                               "operation cost per hour",
                               "boiler assumed output",
                               "cost per btu/hr"]

## comments for the yaml key/value pairs
yaml_comments = deepcopy(bmb.yaml_comments)
yaml_comments["hours of storage for peak"] = "<float>"
yaml_comments["percent at max output"] = "<float>"
yaml_comments["cordwood system efficiency"] = "<float>"
yaml_comments["hours operation per cord"] = "<float>"
yaml_comments["operation cost per hour"] = "<float>"
yaml_comments["energy density"] = "<float>"
yaml_comments["boiler assumed output"] = "<float>"
yaml_comments["cost per btu/hr"] = "<float>"

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = []

## list of prerequisites for module
prereq_comps = deepcopy(bmb.prereq_comps)

DESCRIPTION = """
    This component calculates the potential Heating Oil that could be offset by installing new Wood Boiler. 
"""
