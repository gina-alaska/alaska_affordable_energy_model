
from importlib import import_module

# 
non_component_config_sections = ['community', 'forecast']


def get_config (sections):
    conf = {}
    orders = {}
    comments = {}
    defaults = {}
    for s in sections:
        mod = import_module("aaem.config." + s)
        conf[mod.section_name] = mod.items
        orders[mod.section_name] =  mod.order
        comments[mod.section_name] = mod.comments
        defaults[mod.section_name] = mod.defaults
    return conf, orders, comments, defaults

