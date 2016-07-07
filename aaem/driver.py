"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast
import plot
from diagnostics import diagnostics
from preprocessor import preprocess, Preprocessor
import defaults
from constants import mmbtu_to_kWh, mmbtu_to_gal_HF
import shutil
from pandas import DataFrame, read_csv, concat

import colors

import numpy as np

import yaml
import os.path
from importlib import import_module
from datetime import datetime
import warnings
import sys
try:
    import cPickle as pickle
    #~ print "C Pickle"
except ImportError:
    import pickle




from aaem.components import comp_lib, comp_order



class Driver (object):
    """ 
    Driver for the AAEM.
    """
    
    def __init__ (self, data_dir ,overrides, defaults):
        """ 
        set up driver 
        
        pre:
            infile is an absolute path 
        post:
            model is ready to be run
        """
        self.di= diagnostics()
        try:
            self.cd = CommunityData(data_dir, overrides, defaults, self.di)
        except IOError as e:
            raise RuntimeError, \
                ("A Fatal Error Has occurred, ("+ str(e) +")", self.di)
        try:
            self.fc = Forecast(self.cd, self.di)
        except RuntimeError as e:
            raise RuntimeError, \
                    ("A Fatal Error Has occurred, ("+ str(e) +")", self.di)
        self.load_comp_lib()
        self.plot = False
        
    def toggle_ploting (self):
        """
        toggles plotting feature
        """
        self.plot = not  self.plot
        
    def load_comp_lib (self):
        """
        load the component library
        pre:
            comp_lib.yaml is a library of all available model components
        post:
            self.comp_lib is a dictonarey the maps the names of components in
        absolute defaults, to the python modules. 
        """
        #~ fd = open("comp_lib.yaml", 'r')
        #~ self.comp_lib = yaml.load(fd)
        #~ fd.close()
        self.comp_lib = comp_lib
        self.comp_order = comp_order
        
    def run_components (self):
        """
        run enabled components
        pre:
            self.comp_lib exists
        post:
            self.comps_used is a dictionary of the used components. 
        """
        self.comps_used = {}
        for comp in self.comp_order:
            if self.cd.get_item(comp,"enabled") == False:
                continue
                
            prereq = {}
            pr_list = \
                import_module("aaem.components." +comp_lib[comp]).prereq_comps
            for pr in pr_list:
                prereq[pr] = self.comps_used[pr]
                
            component = self.get_component(self.comp_lib[comp])(self.cd,
                                                                self.fc,
                                                                self.di,
                                                                prereq)
            component.run()
            self.comps_used[comp] = component

    
    def get_component (self, comp_name):
        """
        import a component
        pre:
            comp name is the name of a component
        post:
            returns imported module
        """
        return import_module("aaem.components." + comp_name).component
        
    def save_components_output (self, directory):
        """
        save the output from each component
        pre:
            self.comps_used should be a set of run components
        post:
            for each component in self.comps_used the electric, heating, and
        financial outputs are saved as csv files 
        """
        
        try:
            os.makedirs(os.path.join(directory, "component_outputs/"))
        except OSError:
            pass
    
        for comp in self.comps_used:
            self.comps_used[comp].save_csv_outputs(os.path.join(directory,
                                                          "component_outputs/"))
            self.comps_used[comp].save_additional_output(directory)
    
    def save_forecast_output (self, directory, img_dir):
        """
        save the forecast output:
        pre:
            forecast.save_forecast preconditions are met.
        post: 
            the forecast is saved as a csv file
        """
        self.fc.save_forecast(directory, img_dir, self.plot)
    
    def save_input_files (self, directory):
        """ 
        save the config used
        pre:
            model needs to have been run
        post:
            the nputs used for each component are saved
        """
        self.cd.save_model_inputs(os.path.join(directory,"config_used.yaml"))
    
    def save_diagnostics (self, directory):
        """ 
        save the diagnostics
        pre:
            directory is the location to save the file
        post:
            diagnostics file is saved
        """
        self.di.save_messages(os.path.join(directory,
            self.cd.get_item("community", 'name').replace(" ","_")\
                                                +"_runtime_diagnostics.csv"))
        

def run_model_simple (model_root, run_name, community):
    """
    simple run function 
    
    assumes directory structure used by default in cli
        -model_root
        --setup\
        ---input_data
        ---raw
        --<runs>
        ---config
        ----test_defaults.yaml
        ----<communities>
        ---input_data
        ----<communities>
        ---results
        ----<communities>
    """
    com = community.replace(" ","_")
    overrides = os.path.join(model_root, run_name, "config", 
                                                    com, "community_data.yaml") 
    defaults = os.path.join(model_root, run_name, "config", 
                                                          "test_defaults.yaml")

    input_data = os.path.join(model_root, run_name, "input_data", com)
    out_dir =os.path.join(model_root, run_name, "results", com)
    
    run_model(name = community, override_data = overrides,
              default_data = defaults, input_data = input_data, 
              results_dir = out_dir, results_suffix = None)

def run_model (config_file = None, name = None, override_data = None, 
                            default_data = None, input_data = None,
                            results_dir = None, results_suffix = None, 
                            img_dir = None, plot = False):
    """ 
    run the model given an input file
    pre:
        config_file is the absolute path to a yaml file with this format:
            |------ config example -------------
            |name: #community name
            |overrides: # a path (ex:"..test_case/manley_data.yaml")
            |defaults: # blank or a path
            |output directory path: # a path
            |output directory suffix: TIMESTAMP # TIMESTAMP|NONE|<string>
            |-------------------------------------
            The Following will override the information in the config_file and 
        are optional 
        
        note: if config file is None(not provided) all of these must be provided
            name: is a string (Community Name)
            override_data: a communit_data.yaml file
            default_data: a communit_data.yaml file
            output directory path: path to where outputs should exist
            output directory suffix: suffix to add to directory
    post:
        The model will have been run, and outputs saved.  
    """
    if config_file:
        fd = open(config_file, 'r')
        config = yaml.load(fd)
        fd.close()
    else:
        config = {}
        
    if name:
        config['name'] = name
    if override_data:
        config['overrides'] = override_data
    if default_data:
        config['defaults'] = default_data
    if input_data:
        config['data directory'] = input_data
    if results_dir:
        config['output directory path'] = results_dir
    if results_suffix:
        config['output directory suffix'] = results_suffix
    
    data_dir = os.path.abspath(config['data directory'])
    overrides = os.path.abspath(config['overrides'])
    defaults = "defaults" if config['defaults'] is None else\
                os.path.abspath(config['defaults'])
    
    out_dir = config['output directory path']
    
    out_dir = os.path.abspath(out_dir)

    suffix = config['output directory suffix']
    if suffix == "TIMESTAMP":
        timestamp = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
        out_dir+= "_"  + timestamp 
    elif suffix != "NONE":
        out_dir+= "_" + suffix 
    else:
        pass

    out_dir = os.path.join(out_dir,config['name'],"")
    try:
        os.makedirs(out_dir)
    except OSError:
        pass
    try:
        model = Driver(data_dir, overrides, defaults)
        if plot:
            model.toggle_ploting()
        model.load_comp_lib()
        model.run_components()
        model.save_components_output(out_dir)
        try:
            shutil.copytree(data_dir,os.path.join(out_dir, "input_data"))
            try:
                shutil.copy(os.path.join(data_dir , '..', 
             config['name'].replace(" ", "_") + "_preprocessor_diagnostis.csv"),
                os.path.join(out_dir))
            except IOError:
                pass
        except OSError:
            pass
        model.save_forecast_output(out_dir, img_dir)
        model.save_input_files(out_dir)
        model.save_diagnostics(out_dir) 
    except RuntimeError as e:
        print "Fatal Error see Diagnostics"
        print str(e[0])
        d = e[1]
        d.add_error("FATAL", str(e[0]))
        d.save_messages(os.path.join(out_dir,"diagnostics.csv"))
        model = None
    return model, out_dir

def config_split (root, out):
    """
    find all of the similarities in community data files and pull them out
    pre:
        root: the root of the config directory
            root/
            --comunity1
            --comunity2
              ...
        out: output directory
    """
    root = os.path.abspath(root)
    coms = os.listdir(root)
    ymls = {}
    for com in coms:
        fd = open(os.path.join(root,com,"config_used.yaml"))
        ymls[com] = yaml.load(fd)
        fd.close()
    
    com0 = coms[0]
    common = {}
    for comp in ymls[com0]:
        unit = {}
        del_keys = []
        for key in ymls[com0][comp]:
            inall = True
            for com in coms:
                if com == com0:
                    continue
                if ymls[com][comp][key] != ymls[com0][comp][key]:
                    inall = False
                    break
            if inall:
                unit[key] = ymls[com0][comp][key]
                del_keys.append(key)
        for com in coms:
            for key in del_keys:
                #~ print key
                del ymls[com][comp][key]
        common[comp] = unit
    
    for com in coms:
        del_comps = []
        for comp in ymls[com]:
            #~ print comp + "_" + str(len
            if len(ymls[com][comp]) == 0:
                del_comps.append(comp)
        for comp in del_comps:
            del ymls[com][comp]
        
    fd = open(os.path.join(out,"shared_config.yaml"), 'w')
    text = yaml.dump(common, default_flow_style=False) 
    fd.write(text)
    fd.close()
    
    for com in coms:
        fd = open(os.path.join(out,com,"community_data.yaml"), 'w')
        text = yaml.dump(ymls[com], default_flow_style=False) 
        fd.write(text)
        fd.close()
        
    


def run_batch (config, suffix = "TS", img_dir = None, plot = False):
    """
    run a set of communities
    
    pre:
        config: a library formated {"comunity1, <path to driver file>",
                                    "comunity2, <path to driver file>",...}
                or a .yaml file that would create that when read.
        suffix:
            suffix for the results directory
    post:
        model is run for the communities, and the outputs are saved in a common 
    directory subdivided by community. 
    """
    #~ log = open("Fail.log", 'w')
    try:
        fd = open(config, 'r')
        config = yaml.load(fd)
        fd.close()
    except:
        pass
    #~ communities = {}
    
    if suffix == "TS":
        suffix = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")

    root_path = config[config.keys()[0]].split('config')[0]
    os.makedirs(os.path.join(root_path,'results'))
    picklename = os.path.join(root_path,'results','binary_results.pkl')
    fd = open(picklename, 'wb')
    for key in sorted(config.keys()):
        print key
        #~ try:
        #~ start = datetime.now()
        r_val = run_model(config[key], results_suffix = suffix, 
                          img_dir = img_dir, plot = plot)
                
        pickle.dump([key,{"model": r_val[0], "directory": r_val[1]}], 
                                                    fd, pickle.HIGHEST_PROTOCOL)   
        #~ communities[key] = {"model": r_val[0], "directory": r_val[1]}
        
        del r_val
        #~ print datetime.now() - start
        #~ except StandardError as e :
             #~ log.write("COMMUNITY: " + key + "\n\n")
             #~ log.write( str(sys.exc_info()[0]) + "\n\n")
             #~ log.write( str(e) + "\n\n")
             #~ log.write("--------------------------------------\n\n")
    
    fd.close()
    #~ log.close()
    
    #~ print communities
    return load_results(picklename)
    

def load_results (filename):
    """
    load the results from pickle file
    """
    results = {}
    fd = open(filename, 'rb')
    while True:
        try:
            temp = pickle.load(fd)
            results[temp[0]] = temp[1]
        except:
            break
    fd.close()
    return results





def setup (coms, data_repo, model_root, 
           save_bacth_files = False, run_name = 'run_init',
           setup_intertie = True):
    """
        Set up a model run directory if it does not exist. This is for the first
    time setup. Running it on a directory that exists is unsupported. 
    pre:
        coms: a list of communites
        data_repo: path to the data repo
        model_root: directory to set model up in
        save_batch_files: save the files to run give batches, use full for 
                          development or if running from python directly
    """
    try:
        os.makedirs(os.path.join(model_root, 'setup', "raw_data"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, 'setup', "input_data"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, run_name, "input_data"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, run_name, "config"))
    except OSError:
        pass
    #~ try:
        #~ os.makedirs(os.path.join(model_root, run_name, "results"))
    #~ except OSError:
        #~ pass
    
    model_batch = {}
    for com_id in coms:
        it_batch = {}
        ids = preprocess(data_repo,os.path.join(model_root,
                                                'setup',"input_data"),com_id)
                                                
        if len([id_ for id_ in ids if id_.find('+') == -1]) == 1:
            for idx in range(len(ids)):
                write_config(ids[idx], os.path.join(model_root,run_name))
                model_batch[ids[idx]] = it_batch[ids[idx]] = write_driver(ids[idx],
                                                os.path.join(model_root,run_name))
                
                #~ shutil.copytree(os.path.join(model_root, 'setup',"input_data",
                                             #~ ids[idx].replace(" ", "_")),
                                             #~ os.path.join(model_root, 
                                                #~ run_name,"input_data",
                                                #~ ids[idx].replace(" ", "_")))
                try:
                    os.makedirs(os.path.join(model_root,run_name,
                                            "input_data",ids[idx].replace(" ", "_")))
                except OSError:
                        pass
    
                for fname in Preprocessor.MODEL_FILES.values():
                    try:
                            
                        shutil.copy(os.path.join(model_root, 'setup',
                                    "input_data",ids[idx].replace(" ", "_"),fname),
                                    os.path.join(model_root,run_name,"input_data",
                                                 ids[idx].replace(" ", "_"),fname))
                    except (OSError, IOError):
                        pass
                try:
                    shutil.copy(os.path.join(model_root, 'setup',"input_data",
                        ids[idx].replace(" ", "_") + "_preprocessor_diagnostis.csv"),
                                             os.path.join(model_root,
                                                run_name, "input_data"))
                except IOError:
                    pass
        else:
            ids = [ids[0] + "_intertie"] + ids
            for id in ids: 
                if not setup_intertie:
                    if id.find("intertie") == -1:
                        continue
                        
                write_config(id, os.path.join(model_root,run_name))
                model_batch[id] = it_batch[id] = write_driver(id, 
                                            os.path.join(model_root,run_name))

                try:
                    shutil.copy(os.path.join(model_root, 'setup',"input_data",
                     ids[1].replace(" ", "_") + "_preprocessor_diagnostis.csv"),
                                             os.path.join(model_root,
                                                run_name, "input_data"))
                except IOError:
                    pass

                
                try:
                    os.makedirs(os.path.join(model_root,run_name,
                                        "input_data",id.replace(" ", "_")))
                except OSError:
                    pass

                for fname in Preprocessor.MODEL_FILES.values():
                    try:
                        
                        shutil.copy(os.path.join(model_root, 'setup',
                                    "input_data",id.replace(" ", "_"),fname),
                                os.path.join(model_root,run_name,"input_data",
                                             id.replace(" ", "_"),fname))
                    except (OSError, IOError):
                        pass

        if save_bacth_files:
            fd = open(os.path.join(model_root,
                                com_id.replace(" ", "_") + "_driver.yaml"), 'w')
            text = yaml.dump(it_batch, default_flow_style=False) 
            fd.write("#batch  driver for communities tied to " + com_id +"\n")
            fd.write(text)
            fd.close()
            
    if save_bacth_files:
        fd = open(os.path.join(model_root,"model_driver.yaml"), 'w')
        text = yaml.dump(model_batch, default_flow_style=False) 
        fd.write("#batch  driver for all communities\n")
        fd.write(text)
        fd.close()
    write_defaults(os.path.join(model_root, run_name))
    
    try:
        fd = open(os.path.join(model_root,'setup','raw_data',"VERSION"),'r')
        data_ver = fd.read().replace("\n","")
        fd.close()
    except IOError:
        data_ver = "unknown_version_created_"+ datetime.strftime(datetime.now(),
                                                                "%Y%m%d")
    
    from aaem import __version__ as code_ver
    fd = open(os.path.join(model_root, run_name, "version_metadata.txt"),'w')
    fd.write(("Code Version: " + str(code_ver) + '\n'
              "Data Repo Version: " + str(data_ver) + '\n'))
    
    
    return model_batch
    
def write_defaults(root, my_defaults = None):
    """
    """
    #TODO use my defaults instead
    def_file = open(os.path.join(root, "config", 
                                    "test_defaults.yaml"), 'w')
    def_file.write(yaml.dump(defaults.build_setup_defaults(comp_lib)))
    def_file.close()
                
def write_driver (com_id, root):
    """
    write a drive file
    pre:
        com_id: the community id
        root: the model root
    post:
        the driver file is saved
    """
    driver_text = 'name: ' + com_id.replace(" ","_") + '\n'
    driver_text +=  'overrides: ' + os.path.join(root, "config",
                                                 com_id.replace(" ","_"),
                                                 "community_data.yaml") + '\n'
    driver_text += 'defaults: ' + os.path.join(root,"config",
                                            "test_defaults.yaml") + '\n'
    driver_text += 'data directory: ' + os.path.join(root,
                                                "input_data",
                                                com_id.replace(" ","_")) + '\n'
    driver_text += 'output directory path: ' + os.path.join(root,
                                                 "results") + '\n'
    driver_text += 'output directory suffix: NONE # TIMESTAMP|NONE|<str>\n'
    
    driver_path = os.path.join(root,"config", com_id.replace(" ","_"),
                       com_id.replace(" ", "_") + "_driver.yaml")
    
    try:
        os.makedirs(os.path.join(root, "config", com_id.replace(" ","_")))
    except OSError:
        pass
    driver_file = open(driver_path, 'w')
    driver_file.write(driver_text)
    driver_file.close()
    return driver_path
    
def write_config (com_id, root):
    """
    write community_data yaml for a community
    pre:
        com_id: the community id
        root: the model root
    post:
        the community data file is saved
    """
    config_text = (
"community:\n"
"  name: " + com_id.replace(" intertie","") + " # community provided by user\n"
"  model financial: True # The Financial portion of the model is disabled \n"
)


    #~ print config_text # no coms
    if com_id in ["Barrow", "Nuiqsut"]:
        config_text += (
"  # added to ensure model for north slope \n"
"  natural gas price: 3 # $cost/Mcf <float> (ex. .83)\n"
"  natural gas used: True # is natural gas used in the community\n"
 
)
    #~ print config_text
    try:
        os.makedirs(os.path.join(root, "config", com_id.replace(" ","_")))
    except OSError:
        pass
    config_file = open(os.path.join(root, "config", com_id.replace(" ","_"),
                                                "community_data.yaml"), 'w')
    config_file.write(config_text)
    config_file.close()
    
def run (batch_file, suffix = "TS", img_dir= None, dev = False, plot = False):
    """
    run function
    pre:
        batch_file: a library formated {"comunity1, <path to driver file>",
                                    "comunity2, <path to driver file>",...}
                or a .yaml file that would create that when read.
        suffix:
            suffix for the results directory
        dev: True if you want to see warnings
    post:
        model has been run
    """
    if not dev:
        warnings.filterwarnings("ignore")
    stuff = run_batch(batch_file, suffix,img_dir,plot)
    warnings.filterwarnings("default")
    return stuff
    
    
    
    
    
    
    
    
    
    
    
    
