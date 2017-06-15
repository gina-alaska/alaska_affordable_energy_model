
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
            except (TypeError, KeyError) as e:
                #~ print e
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
                        val_to_write = config[section][item][sub_item]
                        if type(val_to_write) is list:
                            #~ print 'list'
                            for idx in range(len(val_to_write)):
                                if type(val_to_write[idx]) is long:
                                    #~ print 'fixing long'
                                    val_to_write[idx] = int(val_to_write[idx])
                        if type(val_to_write) is long:
                            val_to_write = int(val_to_write)
                        
                        text += str(sub_item) + ': ' + str(val_to_write)
                       
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
                        print config[section][item]
                        raise TypeError, "Bad DataFrame"
                elif type(None) is type(config[section][item]):
                    text += indent + str(item) + ': '
                    try:
                        text +=  ' # ' +  str(comments[section][item]) + nl
                    except KeyError:
                        text += nl
                #### section is a value or list
                else:
                    val_to_write = config[section][item]
                    ## convert longs to ints
                    if type(val_to_write) is list:
                        #~ print 'list'
                        for idx in range(len(val_to_write)):
                            if type(val_to_write[idx]) is long:
                                #~ print 'fixing long'
                                val_to_write[idx] = int(val_to_write[idx])
                    if type(val_to_write) is long:
                        val_to_write = int(val_to_write)
                    #~ print config[section][item]
                    text += indent + str(item) + ': ' + str(val_to_write)
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
    bottom = copy.copy(bottom)
    to_overload = set(top.keys()).intersection( set(bottom.keys()) )
    to_add = set(top.keys()).difference( set(bottom.keys()) )
    #~ print to_overload, to_add
    
    for section in to_overload:
        #~ print section
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
        return False, 'Key missmatch level: ' + str(level) + \
            ". See keys " + str(set(to_validate.keys())^set(validator.keys()))
        
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
                    ## is it a list of types
                    if type(validator[section]) is list:
                        passes_any = False
                        for t in validator[section]:
                            try:
                                t(to_validate[section])
                                passes_any = True
                                break
                            except: 
                                pass
                        ## all types tested none pass
                        if not passes_any:
                            raise ValueError
                            
                    else:# not a list
                        validator[section](to_validate[section])
                except (ValueError, TypeError): 
                    if type(to_validate[section]) is type:
                        reason = 'Type(' + str(validator[section]) + \
                        ') missmatch level: ' + str(level) + '. The type' +\
                        ' was "type" perhaps you are missing a key (' + \
                        section + ') in your config file.'
                    else:
                        reason = 'Type(' + str(validator[section]) + \
                        ') missmatch level: ' + str(level) + '. Type was ' + \
                        str(type(to_validate[section]))+', and the key was ' + \
                        section
                    return False, reason
        
    return True, '' 
    
    
    
ex_data_passes = {
    'a':
        {'1':1, '2':2, '3':{'3-s':3}}, # test subsections
    'a2': {'1':1, '2':2, '3':3}, # test dict
    'b': 3.14, # float
    'c': 10, # int
    'd': 10, # float
    'd2': 10, # float or int
    'd3': DataFrame(), # float or int, or DataFrame
    'e': 10, # str
    'f': '10', # str
    'g': DataFrame([1,2,3]),
    'h': [1,2,3,4]

}
ex_data_fail_1 = {
    'a':
        {'1':1, '2':2, '3':{'3-s':3}}, # test subsections
    'a2': {'1':1, '2':2, '3':3}, # test dict
    'b': 3.14, # float
    'c': 10, # int
    'd': 10, # float
    'd2': 10, # float or int
    'd3': '', # float or int, or DataFrame ## <<<<< fails here
    'e': 10, # str
    'f': '10', # str
    'g': DataFrame([1,2,3]),
    'h': [1,2,3,4]

}
ex_data_fail_2 = {
    'a':
        {'1':1, '2':2, '3':{'3-s':''}}, # test subsections << fails here
    'a2': {'1':1, '2':2, '3':3}, # test dict
    'b': 3.14, # float
    'c': 10, # int
    'd': 10, # float
    'd2': 10, # float or int
    'd3': DataFrame(), # float or int, or DataFrame
    'e': 10, # str
    'f': '10', # str
    'g': DataFrame([1,2,3]),
    'h': [1,2,3,4]

}
## key mismatch
ex_data_fail_3 = {
    'a':
        {'1':1, '2':2, }, # test subsections << fails here
    'a2': {'1':1, '2':2, '3':3}, # test dict
    'b': 3.14, # float
    'c': 10, # int
    'd': 10, # float
    'd2': 10, # float or int
    'd3': DataFrame(), # float or int, or DataFrame
    'e': 10, # str
    'f': '10', # str
    'g': DataFrame([1,2,3]),
    'h': [1,2,3,4]

}

ex_structure = {
    'a':
        {'1':int, '2':int, '3':{'3-s':int}}, # test subsections
    'a2': dict, # test dict
    'b': float, # float
    'c': int, # int
    'd': float, # float
    'd2': [float, int, DataFrame], # float or int
    'd3': [float, int, DataFrame], # float or int, or dataframe
    'e': str, # str
    'f': str, # str
    'g': DataFrame,
    'h': list
}
    
    

