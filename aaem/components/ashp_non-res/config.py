"""
config.py

    Air Source Heat Pumps - Non-Residential config info for community data yaml file
"""
import aaem.components.ashp_base as ashp_base
from copy import deepcopy

COMPONENT_NAME = "Non-Residential ASHP"
IMPORT = "IMPORT"
UNKNOWN = "UNKNOWN"

## List of yaml key/value pairs
yaml = deepcopy(ashp_base.yaml)
yaml[ "btu/hrs"] = 90000
yaml[ "cost per btu/hrs" ] = 25000 

## default values for yaml key/Value pairs
yaml_defaults = deepcopy(ashp_base.yaml_defaults)
    
## order to save yaml
yaml_order = deepcopy(ashp_base.yaml_order) 

## comments for the yaml key/value pairs
yaml_comments = deepcopy(ashp_base.yaml_comments)

## list of data keys not to save when writing the CommunityData output
yaml_not_to_save = deepcopy(ashp_base.yaml_not_to_save)

## list of prerequisites for module
prereq_comps = ['Non-residential Energy Efficiency']
