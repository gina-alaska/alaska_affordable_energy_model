"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast
from diagnostics import diagnostics

from components.residential_buildings import ResidentialBuildings
from components.community_buildings import CommunityBuildings
from components.wastewater import WaterWastewaterSystems

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
        #~ print self.comp_lib
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
            #~ print comp
            component = self.get_component(self.comp_lib[comp])(self.cd,
                                                                self.fc,
                                                                self.di)
            component.run()
            self.comps_used[comp] = component
        
    def update_forecast (self):
        """
        update the forecast totals
        pre:
            residential buildings,community buildings, and water and wastewater
        components need to have been run
        post:
            the forecast totals are up to date
        """
        #~ self.fc.forecast_consumption()
        #~ self.fc.forecast_generation()
        #~ self.fc.forecast_average_kW()
        self.fc.calc_total_HF_forecast()
    
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
    print out_dir
    out_dir = os.path.abspath(out_dir)
    print out_dir
    suffix = config['output directory suffix']
    if suffix == "TIMESTAMP":
        timestamp = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
        out_dir+= "_" +timestamp + '/'
    elif suffix != "NONE":
        out_dir+= "_" + suffix + '/'
    else:
        out_dir+= '/'

    print out_dir
    try:
        os.makedirs(out_dir)
    except OSError:
        pass
    
    
    
    model = Driver(data_dir, overrides, defaults)
    model.load_comp_lib()
    model.run_components()
    model.update_forecast()
    # save functionality needs to be written at component level
    model.save_components_output(out_dir)
    model.save_forecast_output(out_dir)
    model.save_input_files(out_dir)
    model.save_diagnostics(out_dir)
    return model, out_dir

