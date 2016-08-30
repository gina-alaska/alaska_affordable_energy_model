"""
defaults.py

for generating default config structures
"""

from importlib import import_module


import aaem.config as config
from aaem.components import comp_lib, comp_order

def save_config (filename, config, comments, s_order = None, i_orders = None, 
                        indent = '  ' , header = ''):
    """
    write a config yaml file
    
    inputs:
        filename: filename to save file at <string>
        config: dictionary of configs <dict>
        comments: dictionary of comments <dict>
        s_order: (optional) order of sections <list>
        i_orders: (optional) order of items in sections <dict>
        indent: (optional) indent spacing <sting>
        header: (optional) header line <string>
        
    outputs:
        saves config .yaml file at path
    """
    nl = '\n'
    text = '# ' + header + nl
    
    if s_order is None:
        s_order = config.keys()
    
    for section in s_order:
        text += section + ':' + nl
        
        if i_orders is None:
            current_i_order = config[section].keys()
        else: 
            current_i_order = i_orders[section]
            
        for item in current_i_order:
            try:
                text += indent + str(item) + ': ' +  str(config[section][item])
            except KeyError:
                continue
            try:
                text +=  ' # ' +  str(comments[section][item]) 
            except KeyError:
                pass
            
            text += nl
        text += nl + nl        
        
    with open(filename, 'w') as conf:
        conf.write(text)
    
def save_structure ( filename = "default_config.yaml"):
    """
    save the full model structure
    
    input:
        filename
    
    output:
        saves a file
    """
    section_order, conf, orders, comments, defaults = \
                                        gennerate_config_structures()
            
    save_config(filename, conf, comments, section_order, orders,
                            header = "structure of model config file")
    
def gennerate_config_structures ():
    """
    generate all the configuratin structure info
    
    input: none
    
    output:
        returns the desired section order[list], full configuration{dict}, 
            item orders for each section{dict}, comments {dict}, and 
            default values {dict},
    """
    
    conf, orders, comments, defaults = \
            config.get_config(config.non_component_config_sections)
    
    for comp in comp_lib:
        cfg = import_module("aaem.components." + comp_lib[comp]+ '.config')
        
        order = list(cfg.yaml_order) + \
                    list(set(cfg.yaml_order) ^ set(cfg.yaml.keys()))
        orders[comp] = order
        
        conf[comp] = cfg.yaml
        comments[comp] = cfg.yaml_comments
        defaults[comp] = cfg.yaml_defaults
        
        
        
    section_order = config.non_component_config_sections + comp_order
    return section_order, conf, orders, comments, defaults
    

def build_defaults (comp_lib = None):
    """
    build defaults 
    
    input:
        comp_lib: left in for old code
        
    output:
        returns a configuration
    """
    return gennerate_config_structures()[1]


def build_setup_defaults (comp_lib = None):
    """
    build defaults with defaults values filled in
    
    input:
        comp_lib: left in for old code
        
    output:
        returns a configuration
    """
    cfg = gennerate_config_structures()
    conf = cfg[1]
    defaults = cfg[4]
    
    
    for section in defaults:
        for item in defaults[section]:
           conf[section][item] = defaults[section][item]
                      
    
    return conf
