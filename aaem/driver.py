"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast
from diagnostics import diagnostics
from preprocessor import preprocess
import defaults
from constants import mmbtu_to_kWh 
import shutil
from pandas import DataFrame, read_csv, concat

import numpy as np

import yaml
import os.path
from importlib import import_module
from datetime import datetime
import warnings


comp_lib = {
    "residential buildings": "residential_buildings",
    "community buildings": "community_buildings",
    "water wastewater": "wastewater",
        }

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
        #~ fd = open("comp_lib.yaml", 'r')
        #~ self.comp_lib = yaml.load(fd)
        #~ fd.close()
        self.comp_lib = comp_lib
        
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
        self.cd.save_model_inputs(os.path.join(directory,"config_used.yaml"))
    
    def save_diagnostics (self, directory):
        """ 
        save the diagnostics
        pre:
            directory is the location to save the file
        post:
            diagnostics file is saved
        """
        self.di.save_messages(os.path.join(directory,"diagnostics.csv"))
        


def run_model (config_file, name = None, override_data = None, 
                            default_data = None, input_data = None,
                            results_dir = None, results_suffix = None):
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
    
    model = Driver(data_dir, overrides, defaults)
    model.load_comp_lib()
    model.run_components()
    model.save_components_output(out_dir)
    shutil.copytree(data_dir,os.path.join(out_dir, "input_data"))
    model.save_forecast_output(out_dir)
    model.save_input_files(out_dir)
    
    try:
        create_generation_forecast([model],out_dir)
        
    except IndexError:
        model.diagnostics.add_waring("Generation Forecast", 
                                        "Cannont Create File")
    model.save_diagnostics(out_dir)  
    return model, out_dir

def config_split (root, out):
    """
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
        
    


def run_batch (config, suffix = "TS"):
    """ Function doc """
    try:
        fd = open(config, 'r')
        config = yaml.load(fd)
        fd.close()
    except:
        pass
    communities = {}
    if suffix == "TS":
        suffix = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
    for key in config:
        print key
        r_val = run_model(config[key], results_suffix = suffix)
        communities[key] = {"model": r_val[0], "directory": r_val[1]}
    return communities

def setup (coms, data_repo, model_root, save_bacth_files = False):
    """
    """
    try:
        os.makedirs(os.path.join(model_root, 'setup',"raw_data"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, 'setup',"input_data"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, 'run_init',"input_data"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, 'run_init', "config"))
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(model_root, 'run_init', "results"))
    except OSError:
        pass
    
    model_batch = {}
    for com_id in coms:
        it_batch = {}
        ids = preprocess(data_repo,os.path.join(model_root,
                                                'setup',"input_data"),com_id)
        if len(ids) == 1:
            write_config(ids[0], os.path.join(model_root,"run_init"))
            model_batch[ids[0]] = it_batch[ids[0]] = write_driver(ids[0], os.path.join(model_root,"run_init"))
            shutil.copytree(os.path.join(model_root, 'setup',"input_data",ids[0].replace(" ", "_")),os.path.join(model_root, 'run_init',"input_data",ids[0].replace(" ", "_")))
        else:
            ids = [ids[0] + " intertie"] + ids
            for id in ids:
                
                if id.find("intertie") == -1:
                    continue
                write_config(id, os.path.join(model_root,"run_init"))
                model_batch[id] = it_batch[id] = write_driver(id, os.path.join(model_root,"run_init"))
                shutil.copytree(os.path.join(model_root, 'setup',"input_data",id.replace(" ", "_")),os.path.join(model_root, 'run_init',"input_data",id.replace(" ", "_")))
                
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
    write_defaults(os.path.join(model_root, 'run_init'))
    return model_batch
    
def write_defaults(root, my_defaults = None):
    """
    """
    #TODO use my defaults instead
    def_file = open(os.path.join(root, "config", 
                                    "test_defaults.yaml"), 'w')
    def_file.write(defaults.for_setup)
    def_file.close()
                
def write_driver (com_id, root):
    """ Function doc """
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
    """ Function doc """
    config_text = (
"community:\n"
"  name: " + com_id.replace(" intertie","") + " # community provided by user\n"
"  model financial: False # The Financial portion of the model is disabled \n"
)


    #~ print config_text
    if com_id in ["Valdez","Sitka"]:
        config_text += (
"  # added to ensure model execution for weird communities (valdez & sitka) \n"
"  res non-PCE elec cost: -9999 # $cost/kWh <float> (ex. .83)\n"
"  elec non-fuel cost: -9999 # $cost/kWh <float> (ex. .83)\n"
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

    
    
def create_generation_forecast (models, path):
    """  
    creates the generation forecast file
    pre:
        models: a list of driver objects, the generation total from models[0] is
    used as the total
        path: path to an existing directory
    post:
        a file is saved in path's directory
    """
    gen_fc = None
    nat_gas = False
    name = models[0].cd.get_item('community', 'name')
    for idx in range(len(models)):
        if idx == 0:
            
            gen_fc = concat([models[idx].fc.generation, 
                             models[idx].cd.get_item('community',
                                                  'generation numbers')], 
                                                                    axis = 1)
            gen_fc["generation total"] = \
                               gen_fc['total_electricity_generation [kWh/year]']
            del gen_fc['total_electricity_generation [kWh/year]']
            continue
        gen_fc = gen_fc + models[idx].cd.get_item('community',
                                                 'generation numbers')
   
    for col in ('generation hydro', 'generation natural gas',
                'generation wind', 'generation solar',
                'generation biomass'):
        try:

            last = gen_fc[gen_fc[col].notnull()]\
                                [col].values[-3:]
            last =  np.mean(last)
            last_idx = gen_fc[gen_fc[col].notnull()]\
                                [col].index[-1]
                                
                                
            col_idx = np.logical_and(gen_fc[col].isnull(), 
                                     gen_fc[col].index > last_idx)
                                     
            gen_fc[col][col_idx] = last
        except IndexError:
            pass
                
                                    
    last_idx = gen_fc[gen_fc['generation diesel'].notnull()]\
                            ['generation diesel'].index[-1]


    col = gen_fc[gen_fc.index>last_idx]\
                                ['generation total']\
          - gen_fc[gen_fc.index>last_idx][['generation hydro', 
                                           'generation natural gas',
                                        'generation wind', 'generation solar',
                                         'generation biomass']].fillna(0).sum(1)
    
    gen_fc.loc[gen_fc.index>last_idx,'generation diesel'] = col
    
    
    for col in ['generation total', 'generation diesel', 'generation hydro', 
                'generation natural gas', 'generation wind', 
                'generation solar', 'generation biomass']:
        gen_fc[col.replace(" ", "_") + " [kWh/year]"] = \
                                    gen_fc[col].fillna(0).round().astype(int)
        gen_fc[col.replace(" ", "_") + " [mmbtu/year]"] = \
                    (gen_fc[col] / mmbtu_to_kWh).fillna(0).round().astype(int)
        del gen_fc[col]
    
    
    gen_fc.index = gen_fc.index.values.astype(int)
    gen_fc = gen_fc.fillna(0).ix[2003:]
    
    out_file = os.path.join(path, name + "_generation_forecast.csv")
    fd = open(out_file, 'w')
    fd.write("# Generation forecast\n")
    fd.write("# projections start in " + str(int(last_idx+1)) + "\n")
    fd.close()
    gen_fc.to_csv(out_file, index_label="year", mode = 'a')   
    return gen_fc
    
    
def run (batch_file, suffix = "TS", dev = False):
    """ Function doc """
    if not dev:
        warnings.filterwarnings("ignore")
    stuff = run_batch(batch_file, suffix)
    warnings.filterwarnings("default")
    return stuff
    
    
    
    
    
    
    
    
    
    
    
    
