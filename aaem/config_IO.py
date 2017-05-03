
import yaml
from aaem.yaml_dataframe import dict_to_dataframe
from pandas import DataFrame
import aaem.yaml_dataframe as yd
import copy

def read_config (filename):
    """
    """
    with open(filename, 'r') as conf_text:
        conf = yaml.load(conf_text)
    
    
    for section in conf:
        for item in conf[section]:
            try:
                conf[section][item] = dict_to_dataframe(conf[section][item])
            except (TypeError, KeyError):
                pass
    
    
    return conf


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
    # add header
    text = '# ' + header + nl
    
    ## get default order if not provided
    if s_order is None:
        s_order = config.keys()
    
    
    ## for each section
    for section in s_order:
        ### add section
        text += section + ':' + nl
        
        ### get order
        if i_orders is None:
            current_i_order = config[section].keys()
        else: 
            current_i_order = i_orders[section]
          
        ### add each item
        for item in current_i_order:
            
            #### section is a dict
            try:
                if type(config[section][item]) is dict:
                    
                    text += indent + str(item) + ': '
                    try: 
                        text +=  ' # ' +  str(comments[section][item]) 
                    except KeyError:
                        pass
                    text += nl
                    for sub_item in config[section][item]:
                        text += indent + indent
                        text += str(sub_item) + ': '  +\
                                str(config[section][item][sub_item])
                       
                        text += nl
                    continue
            except KeyError as e:
                pass
            
           
            try: 
                #### section is a DataFrame
                if DataFrame == type(config[section][item]):
                    text += indent + str(item) + ': ' 
                    try:
                        text +=  ' # ' +  str(comments[section][item]) + nl
                    except KeyError:
                        text += nl
                    try:
                        text += yd.dataframe_to_yaml_snippet(
                            config[section][item],
                            indent,
                            2,
                            nl) 
                    except TypeError:
                        raise TypeError, "Bad DataFrame"
                #### section is a value
                else:
                    #~ print section, config[section][item]
                    text += indent + str(item) + ': ' + \
                        str(config[section][item]) 
                    try:
                        text +=  ' # ' +  str(comments[section][item]) + nl
                    except KeyError:
                        text += nl
            except KeyError:
                continue
                
        ### add double newlines to end of each section
        text += nl + nl        
        
    ### save
    with open(filename, 'w') as conf:
        conf.write(text)


        
        
def merge_configs (bottom, top):
    """merge two configs with values in 'top' overwriting valus in  
    'bottom' if two keys are the same
    """
    # make an explict copy
    bottom = copy.deepcopy(bottom)
    to_overload = set(top.keys()).intersection( set(bottom.keys()) )
    to_add = set(top.keys()).difference( set(bottom.keys()) )
    #~ print to_overload, to_add
    
    for section in to_overload:
        if type(bottom[section]) is dict:
            try:
                bottom[section] = merge_configs(bottom[section], top[section])
                continue
            except AttributeError:
                pass
        
        bottom[section] = top[section]
    
    for section in to_add:
        bottom[section] = top[section]
    
    return bottom

def validate_dict(to_validate, validator, level = 0):
    """validate a dictionarys structure
    """
    ## are all keys same?
    if set(to_validate.keys()) != set(validator.keys()):
        return False, 'Key missmatch level: ' + str(level) 
        
    for section in to_validate:
        ## if to_validate is a sub dictionary
        if type(to_validate[section]) is dict:
            if type(validator[section]) is dict:
                boolean, reason = validate_dict(to_validate[section],
                    validator[section], level + 1)
                if False == boolean:
                    return boolean, reason
            else:# type(validator[section]) is type: 
                if type(to_validate[section])!= dict:
                    return False, 'Type(dict) missmatch level: ' + str(level) 
        # if to_validate is a value
        else: 
            if type(to_validate[section]) != validator[section]:
                
                try:
                    # if the type can convert to desired type don't fail
                    validator[section](to_validate[section])
                except ValueError: 
                    reason = 'Type(' + str(validator[section]) + \
                        ') missmatch level: ' + str(level) 
                    return False, reason
        
    return True, '' 
    
    
    
    
    
    
    

