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


from aaem import __version__
from aaem.components import comp_lib, comp_order

import zipfile


class Driver (object):
    """ 
    Driver for the AAEM.
    """
    def __init__ (self, model_root, community):
        """ 
        set up driver 
        
        pre:
            infile is an absolute path 
        post:
            model is ready to be run
        """
        self.model_root = model_root
        self.di = diagnostics()
        self.community = community.replace(' ', '_')
        self.data_dir = os.path.join(model_root, 'input_data', self.community)
        self.community_config = os.path.join(model_root, 'config', self.community, 'community_data.yaml')
        self.global_config = os.path.join(model_root, 'config', 'test_defaults.yaml')
        
    
    
    
    def setup ():
        """ Function doc """
        try:
            self.cd = CommunityData(self.data_dir,
                                    self.community_config, 
                                    self.global_config, 
                                    self.di)
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
        self.plot = not self.plot
        
    def load_comp_lib (self):
        """
        load the component library
        pre:
            comp_lib.yaml is a library of all available model components
        post:
            self.comp_lib is a dictonarey the maps the names of components in
        absolute defaults, to the python modules. 
        """
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
                import_module("aaem.components." + comp_lib[comp]).prereq_comps
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
            the inputs used for each component are saved
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
        
    def run (self, model_root, scalers):
        """
        model root ./model/m0.18.0... 
        """
        self.load_comp_lib()
        self.run_components()
        self.save_components_output(out_dir)
        self.copy_inputs() 
        
        self.save_forecast_output(out_dir, img_dir)
        self.save_input_files(out_dir)
        self.save_diagnostics(out_dir) 
        
        return self, out_dir
    


class Setup (object):
    """ Class doc """
    
    def __init__ (self, model_root, communities, data_repo, tag = None):
        """ Class initialiser """
        self.model_root = model_root
        self.communities = communities
        self.data_repo = data_repo
        
        self.tag = tag
        if tag is None:
            self.tag = make_version_tag
        #~ self.raw_directory = os.path.join(model_root, 'setup', "raw_data")
        #~ self.preprocessed_directory = \
                #~ os.path.join(model_root, 'setup', "input_data")
                
                
    def make_version_tag (self):
        """ Function doc """
        data_version_file = os.path.join(self.data_repo, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
            ver = 'm' +  __version__  + '_d' + ver
        return ver
        
    def setup_directories (self):
        """ Function doc """
        setup_path = os.path.join(self.model_root, self.tag)
    
        try:
            os.makedirs(os.path.join(setup_path, "input_files"))
        except OSError:
            pass
        try:
            os.makedirs(os.path.join(setup_path, "config"))
        except OSError:
            pass
            
    def setup_community_configs (self, coms = None):
        """ Function doc """
        config_path = os.path.join(self.model_root, self.tag, 'config')
        
        if coms is None:
            coms = self.communities
        
        for c in coms:
            config = {'community':{'name': c,
                                   'model financial': True,},
                        }
            comments = {'community':{'name': 'name of community/project',
                                     'model financial': 'Model Finances?',},
               
                        }
            north_slope = ["Barrow", "Nuiqsut"] 
            if c.split('+')[0] in north_slope or c.split('_')[0] in north_slope:
                config['community']['natural gas price'] = 3
                config['community']['natural gas used'] = True
                comments['community']['natural gas price'] = 'LNG price $/gal'
                comments['community']['natural gas used'] = \
                                                        'LNG used in community'
            
            config_file = os.path.join(config_path, 
                                c.replace(' ','_') + '_community_data.yaml')
            header = 'community data for ' + c 
            write_config_file(config_file, config, comments, 
                                            s_order = ['community',],
                                            i_orders = {'community':['name',
                                                        'model financial',
                                                        'natural gas used',
                                                        'natural gas price']},
                                            header = header)
        
    def setup_global_config (self):
        """ Function doc """
        config_path = os.path.join(self.model_root, self.tag, 'config', 
                                                    "__golbal_config.yaml")
        with open(config_path, 'w') as def_file:
            def_file.write(yaml.dump(defaults.build_setup_defaults(comp_lib),
                                                default_flow_style = False))
            
    def setup_input_files (self):
        """ Function doc """
        input_path = os.path.join(self.model_root,self.tag,"input_files")
        
        ids = self.preprocess_input_files(input_path)
        self.move_input_files_diagnostics(input_path)
        self.write_input_files_metadata(input_path)
        self.archive_input_files_raw_data (input_path)
        return ids
        
    def preprocess_input_files (self, input_path):
        all_ids = []
        for c in self.communities:
            it_batch = {}
            ids = preprocess(self.data_repo, input_path, c, dev = True)
            all_ids += ids
            
        return all_ids
            
    def move_input_files_diagnostics (self, input_path):
        diag_path = os.path.join(input_path, '__diagnostic_files')
        try:
            os.makedirs(diag_path)
        except OSError:
            pass
        for diagf in [f for f in os.listdir(input_path) if '.csv' in f] : 
            os.rename(os.path.join(input_path,diagf),
                        os.path.join(diag_path,diagf))
          
    def write_input_files_metadata (self, input_path ):
        """ Function doc """
        data_version_file = os.path.join(self.data_repo, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
        with open(os.path.join(input_path,
                            'input_files_metadata.yaml'), 'w') as meta:
            meta.write(yaml.dump({'upadted': datetime.strftime(datetime.now(),
                                                        "%Y-%m-%d %H:%M:%S"),
                                  'data version': ver},
                                  default_flow_style = False))
                                  
    def archive_input_files_raw_data (self, input_path):
        """ """
        data_version_file = os.path.join(self.data_repo, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
    
        z = zipfile.ZipFile(os.path.join(input_path, "raw_data.zip"),"w")
        for raw in [f for f in os.listdir(self.data_repo) if '.csv' in f]:
            z.write(os.path.join(self.data_repo,raw), raw)
        z.write(os.path.join(data_version_file), 'VERSION')

        
    def setup (self, force = False):
        """ Function doc """
        setup_path = os.path.join(self.model_root, self.tag)
        if os.path.exists(setup_path) and force == False:
            return False
            
        self.setup_directories()
        self.setup_global_config()
        ids = self.setup_input_files()
        self.setup_community_configs(ids)
        return True
        
        
def write_config_file(path, config, comments, s_order = None, i_orders = None, indent = '  ' , header = ''):
    """
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
        
    with open(path, 'w') as conf:
        conf.write(text)
    
    
            
    
    
    
    
    
