"""
defaults.py

for generating default config structures
"""
from importlib import import_module


import aaem.config as config
from aaem.components import comp_lib, comp_order
import aaem.yaml_dataframe as yd

from pandas import DataFrame

def save_formated_generation_numbers (generation_numbers, indent = '  ', nl = '\n'):
    text = ""
    for row in [
        'year', 
        'generation diesel',
        'generation hydro',
        'generation wind',
        'generation solar',
        'generation natural gas',
        'generation biomass',
    ]:
        text += indent * 2 + row +': ' + str(generation_numbers[row]) + nl
    #~ print text
    return text
    


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
                if type(config[section][item]) is dict:
                    
                    text += indent + str(item) + ': '
                    try: 
                        text +=  ' # ' +  str(comments[section][item]) 
                    except KeyError:
                        pass
                    text += nl
                    #~ print section, item
                    #~ print type(config[section][item])
                    #~ 
    
                        #~ text += yd.dataframe_to_yaml_snippet(config[section][item], indent, 2, nl)
                        #~ print text
                    #~ else:
                    for sub_item in config[section][item]:
                        text += indent + indent
                        text += str(sub_item) + ': '  +\
                                str(config[section][item][sub_item])
                       
                        text += nl
                    continue
            except KeyError as e :
                #~ print e
                pass
            
            try:
                if DataFrame == type(config[section][item]):
                    #~ print section,item
                    #~ print  config[section][item]
                    text += indent + str(item) + ': ' 
                    try:
                        text +=  ' # ' +  str(comments[section][item]) + nl
                    except KeyError:
                        text += nl
                    try:
                        text += yd.dataframe_to_yaml_snippet(config[section][item],
                        indent, 2, nl) 
                    except TypeError:
                        text += indent * 2 + "NOTE: None Need to fix" + nl
                else:
                    text += indent + str(item) + ': ' + \
                        str(config[section][item]) 
                    try:
                        text +=  ' # ' +  str(comments[section][item]) + nl
                    except KeyError:
                        text += nl
            except KeyError:
                continue
            
            
            #~ text += nl
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
