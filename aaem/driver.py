"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast
from diagnostics import diagnostics
from preprocessor import preprocess
import defaults


from pandas import DataFrame, read_pickle, read_csv
import numpy as np

import yaml
import os.path
from importlib import import_module
from datetime import datetime

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
        self.cd = CommunityData(data_dir, overrides,defaults)
        self.fc = Forecast(self.cd, self.di)
        self.load_comp_lib()
        
    def load_comp_lib (self):
        """
        load the component library
        pre:
            comp_lib.yaml is a library of all available model components
        post:
            self.comp_lib is a dictonarey the maps the names of components in
        absolute defaults, to the python modules. 
        """
        fd = open("comp_lib.yaml", 'r')
        self.comp_lib = yaml.load(fd)
        fd.close()
        
    def run_components (self):
        """
        run enabled components
        pre:
            self.comp_lib exists
        post:
            self.comps_used is a dictionary of the used components. 
        """
        self.comps_used = {}
        for comp in self.comp_lib:
            if self.cd.get_item(comp,"enabled") == False:
                continue
            component = self.get_component(self.comp_lib[comp])(self.cd,
                                                                self.fc,
                                                                self.di)
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
        return import_module("components." + comp_name).component
        
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
            os.makedirs(directory + "model_outputs/")
        except OSError:
            pass
    
        for comp in self.comps_used:
            self.comps_used[comp].save_csv_outputs(directory + "model_outputs/")
    
    def save_forecast_output (self, directory):
        """
        save the forecast output:
        pre:
            forecast.save_forecast preconditions are met.
        post: 
            the forecast is saved as a csv file
        """
        self.fc.save_forecast(directory)
    
    def save_input_files (self, directory):
        """ 
        save the config used
        pre:
            model needs to have been run
        post:
            the nputs used for each component are saved
        """
        self.cd.save_model_inputs(directory+"config_used.yaml")
    
    def save_diagnostics (self, directory):
        """ 
        save the diagnostics
        pre:
            directory is the location to save the file
        post:
            diagnostics file is saved
        """
        self.di.save_messages(directory+"diagnostics.csv")
        


def run_model (config_file):
    """ 
    run the model given an input file
    pre:
        config_file is the absolute path to a yaml file with this format:
            |------ config example -------------
            |overrides: # a path (ex:"..test_case/manley_data.yaml")
            |defaults: # blank or a path
            |output directory path: # a path
            |output directory suffix: TIMESTAMP # TIMESTAMP|NONE|<string>
            |-------------------------------------
    post:
        The model will have been run, and outputs saved.  
    """
    fd = open(config_file, 'r')
    config = yaml.load(fd)
    fd.close()
    
    
    data_dir = os.path.abspath(config['data directory'])
    overrides = os.path.abspath(config['overrides'])
    defaults = "defaults" if config['defaults'] is None else\
                os.path.abspath(config['defaults'])
    
    
    
    out_dir = config['output directory path']
    
    out_dir = out_dir[:-1] if out_dir[-1] == '/' else out_dir 
    out_dir = os.path.abspath(out_dir)
    suffix = config['output directory suffix']
    if suffix == "TIMESTAMP":
        timestamp = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
        out_dir+= "_" +timestamp + '/'
    elif suffix != "NONE":
        out_dir+= "_" + suffix + '/'
    else:
        out_dir+= '/'

    try:
        os.makedirs(out_dir)
    except OSError:
        pass
    
    
    
    model = Driver(data_dir, overrides, defaults)
    model.load_comp_lib()
    model.run_components()
    model.save_components_output(out_dir)
    model.save_forecast_output(out_dir)
    model.save_input_files(out_dir)
    model.save_diagnostics(out_dir)
    return model, out_dir



def run_batch (config):
    """ Function doc """
    try:
        fd = open(config, 'r')
        config = yaml.load(fd)
        fd.close()
    except:
        pass
    communities = {}
    for key in config:
        r_val = run_model(config[key])
        communities[key] = {"model": r_val[0], "directory": r_val[1]}
    return communities
    

def setup (community, data_repo, model_directory):
    """ Function doc """
    directory = os.path.abspath(model_directory)
    try:
        os.makedirs(os.path.join(directory,"config"))
    except OSError:
        while True:
            resp = raw_input("The directory "+ directory + " already exists" +\
                             " would you like to over right any model data" +\
                             " in it? (y or n): ")
            if resp.lower() == "y":
                break
            elif resp.lower() == "n":
                return
            else:
                pass
                
    config_text = "community:\n  name: " + community +\
                  " # community provided by user\n"
    config_file = open(os.path.join(directory, "config",
                                    "community_data.yaml"), 'w')
    config_file.write(config_text)
    config_file.close()
    def_file = open(os.path.join(directory, "config", 
                                    "test_defaults.yaml"), 'w')
    def_file.write(defaults.for_setup)
    def_file.close()
    
    driver_text =  'overrides: ' + os.path.join(directory,"config",
                                                "community_data.yaml") + '\n'
    driver_text += 'defaults: ' + os.path.join(directory,"config",
                                                "test_defaults.yaml") + '\n'
    driver_text += 'data directory: ' + os.path.join(directory,
                                                "input_data") + '\n'
    driver_text += 'output directory path: ' + os.path.join(directory,
                                                 "results") + '\n'
    driver_text += 'output directory suffix: NONE # TIMESTAMP|NONE|<str>\n'
    
    driver_file = open(os.path.join(directory, 
                       community.replace(" ", "_") + "_driver.yaml"), 'w')
    driver_file.write(driver_text)
    driver_file.close()
    
    preprocess(data_repo,os.path.join(directory,"input_data"),community)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
