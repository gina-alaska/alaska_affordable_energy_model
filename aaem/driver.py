"""
driver.py

    will run the model
"""
from community_data import CommunityData
from forecast import Forecast
import plot
from diagnostics import diagnostics
from preprocessor import preprocess, MODEL_FILES
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
import sys


comp_lib = {
    "residential buildings": "residential_buildings",
    "non-residential buildings": "community_buildings",
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
            self.comps_used[comp].save_additional_output(directory)
    
    def save_forecast_output (self, directory, img_dir):
        """
        save the forecast output:
        pre:
            forecast.save_forecast preconditions are met.
        post: 
            the forecast is saved as a csv file
        """
        self.fc.save_forecast(directory, img_dir)
    
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
                            img_dir = None):
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
        
        try:
            try:
                gfc_img_dir = os.path.join(img_dir,'generation_forecast')
                os.makedirs(gfc_img_dir)
                
            except OSError:
                pass
            #~ start = datetime.now() 
            create_generation_forecast([model],out_dir, gfc_img_dir)
            #~ print "saving generation fc:" + str( datetime.now() - start)
        except (IndexError, KeyError):
            model.di.add_warning("Generation Forecast", 
                                            "Cannont Create File")
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
        
    


def run_batch (config, suffix = "TS", img_dir = None):
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
    communities = {}
    
    if suffix == "TS":
        suffix = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
    for key in config:
        print key
        #~ try:
        #~ start = datetime.now()
        r_val = run_model(config[key], results_suffix = suffix, 
                          img_dir = img_dir)
        communities[key] = {"model": r_val[0], "directory": r_val[1]}
        #~ print datetime.now() - start
        #~ except StandardError as e :
             #~ log.write("COMMUNITY: " + key + "\n\n")
             #~ log.write( str(sys.exc_info()[0]) + "\n\n")
             #~ log.write( str(e) + "\n\n")
             #~ log.write("--------------------------------------\n\n")
             
    #~ log.close()
    return communities
    
def res_log (coms, dir3):
    """
    """
    out = []
    for c in coms:
        if c.find("_intertie") != -1:
            continue
        try:
            res = coms[c]['model'].comps_used['residential buildings']
            out.append([c,
                res.get_NPV_benefits(),res.get_NPV_costs(),
                res.get_NPV_net_benefit(),res.get_BC_ratio(),
                res.diesel_prices[0], res.init_HH, res.opportunity_HH,
                res.baseline_HF_consumption[0],
                res.baseline_HF_consumption[0] - res.refit_HF_consumption[0],
                round(float(res.fuel_oil_percent)*100,2)])
        except KeyError:
            pass
    data = DataFrame(out,columns = ['community','NPV Benefit','NPV Cost', 
                           'NPV Net Benefit', 'B/C Ratio',
                           'Heating Oil Price - year 1',
                           'Occupied Houses', 'Houses to Retrofit', 
                           'Heating Oil Consumed(gal) - year 1',
                           'Heating Oil Saved(gal/year)',
                           'Heating Oil as percent of Total Heating Fuels']
                    ).set_index('community').round(2)
    f_name = os.path.join(dir3,'residential_summary.csv')
    fd = open(f_name,'w')
    fd.write("# residental building component summary by community\n")
    fd.close()
    data.to_csv(f_name, mode='a')
    
def com_log (coms, dir3): 
    """
    """
    out = []
    for c in coms:
        if c.find("_intertie") != -1:
            continue
        try:
            com = coms[c]['model'].comps_used['non-residential buildings']
            out.append([c,
                com.get_NPV_benefits(),com.get_NPV_costs(),
                com.get_NPV_net_benefit(),com.get_BC_ratio(),
                com.diesel_prices[0], com.elec_price[0], 
                com.num_buildigns , com.refit_sqft_total,
                com.baseline_HF_consumption,
                com.baseline_kWh_consumption,
                com.baseline_HF_consumption - com.refit_HF_consumption,
                com.baseline_kWh_consumption - com.refit_kWh_consumption])
        except KeyError:
            pass
    data = DataFrame(out,columns = ['community','NPV Benefit','NPV Cost', 
                           'NPV Net Benefit', 'B/C Ratio',
                           'Heating Oil Price - year 1','$ per kWh - year 1',
                           'Number Buildings', 'Total Square Footage', 
                           'Heating Oil Consumed(gal) - year 1',
                           'Electricity Consumed(kWh) - year 1',
                           'Heating Oil Saved(gal/year)',
                           'Electricity Saved(kWh/year)'
                           ]
                    ).set_index('community').round(2)
    f_name = os.path.join(dir3,'non-residential_summary.csv')
    fd = open(f_name,'w')
    fd.write("# non residental building component summary by community\n")
    fd.close()
    data.to_csv(f_name, mode='a')
    
def village_log (coms, dir3): 
    """
    """
    out = []
    for c in coms:
        if c.find("_intertie") != -1:
            continue
        
        try:
            res = coms[c]['model'].comps_used['residential buildings']
            res_con = [res.baseline_HF_consumption[0], np.nan]
            res_cost = [res.baseline_HF_cost[0], np.nan]
        except KeyError:
            res_con = [np.nan, np.nan]
            res_cost = [np.nan, np.nan]
        try:
            com = coms[c]['model'].comps_used['non-residential buildings']
            com_con = [com.baseline_HF_consumption,com.baseline_kWh_consumption]
            com_cost = [com.baseline_HF_cost[0],com.baseline_kWh_cost[0]]
        except KeyError:
            com_con = [np.nan, np.nan]
            com_cost = [np.nan, np.nan]
        try:
            ww = coms[c]['model'].comps_used['water wastewater']
            ww_con = [ww.baseline_HF_consumption[0],
                            ww.baseline_kWh_consumption[0]]
            ww_cost = [ww.baseline_HF_cost[0],ww.baseline_kWh_cost[0]]
        except KeyError:
            ww_con = [np.nan, np.nan]
            ww_cost = [np.nan, np.nan]
        t = [c, coms[c]['model'].cd.get_item('community','region')] +\
            res_con + com_con + ww_con + res_cost + com_cost + ww_cost 
        out.append(t)
    start_year = 2017
    data = DataFrame(out,columns = ['community','Region',
                    'Residential Heat (MMBTU)', 
                    'Residential Electricity (MMBTU)',
                    'Non-Residential Heat (MMBTU)', 
                    'Non-Residential Electricity (MMBTU)',
                    'Water/Wastewater Heat (MMBTU)', 
                    'Water/Wastewater Electricity (MMBTU)',
                    'Residential Heat (cost ' + str(start_year)+')', 
                    'Residential Electricity (cost ' + str(start_year)+')',
                    'Non-Residential Heat (cost ' + str(start_year)+')',
                    'Non-Residential Electricity (cost ' + str(start_year)+')',
                    'Water/Wastewater Heat (cost ' + str(start_year)+')', 
                    'Water/Wastewater Electricity (cost ' + str(start_year)+')',
                    ]
                    ).set_index('community')
    f_name = os.path.join(dir3,'village_sector_consumption_summary.csv')
    fd = open(f_name,'w')
    fd.write("# summary of consumption and cost\n")
    fd.close()
    data.to_csv(f_name, mode='a')


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
        if len(ids) == 1:
            write_config(ids[0], os.path.join(model_root,run_name))
            model_batch[ids[0]] = it_batch[ids[0]] = write_driver(ids[0],
                                            os.path.join(model_root,run_name))
            
            #~ shutil.copytree(os.path.join(model_root, 'setup',"input_data",
                                         #~ ids[0].replace(" ", "_")),
                                         #~ os.path.join(model_root, 
                                            #~ run_name,"input_data",
                                            #~ ids[0].replace(" ", "_")))
            try:
                os.makedirs(os.path.join(model_root,run_name,
                                        "input_data",ids[0].replace(" ", "_")))
            except OSError:
                    pass

            for fname in MODEL_FILES.values():
                try:
                        
                    shutil.copy(os.path.join(model_root, 'setup',
                                "input_data",ids[0].replace(" ", "_"),fname),
                                os.path.join(model_root,run_name,"input_data",
                                             ids[0].replace(" ", "_"),fname))
                except (OSError, IOError):
                    pass
            try:
                shutil.copy(os.path.join(model_root, 'setup',"input_data",
                    ids[0].replace(" ", "_") + "_preprocessor_diagnostis.csv"),
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

                for fname in MODEL_FILES.values():
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
    def_file.write(defaults.for_setup)
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


    #~ print config_text
    if com_id in ["Valdez"]:
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

    
    
def create_generation_forecast (models, path, img_dir = None):
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
    population = models[0].fc.population
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
                
    
    #~ print not np.isnan(gen_fc[['generation natural gas']]).all().bool()
    if not np.isnan(gen_fc[['generation natural gas']]).all().bool():
        for col in ('generation hydro', 'generation diesel',
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
        last_idx = gen_fc[gen_fc['generation natural gas'].notnull()]\
                                ['generation natural gas'].index[-1]
    
    
        
        col = gen_fc[gen_fc.index>last_idx]\
                                    ['generation total']\
              - gen_fc[gen_fc.index>last_idx][['generation hydro', 
                                               'generation diesel',
                                            'generation wind', 'generation solar',
                                             'generation biomass']].fillna(0).sum(1)
        
        gen_fc.loc[gen_fc.index>last_idx,'generation natural gas'] = col
    else:
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
    
    gen_fc["community"] = name
    order =  [gen_fc.columns[-1]] + gen_fc.columns[:-1].values.tolist()
    
    gen_fc = concat([population.astype(int),gen_fc], axis=1)
    
    
    order.insert(1,"population")
    gen_fc.index = gen_fc.index.values.astype(int)
    gen_fc = gen_fc.fillna(0).ix[2003:]
   
    png_list = ['population',
    'generation_total [mmbtu/year]',
    'generation_diesel [mmbtu/year]',
    'generation_hydro [mmbtu/year]',
    'generation_natural_gas [mmbtu/year]',
    'generation_wind [mmbtu/year]',
    'generation_solar [mmbtu/year]',
    'generation_biomass [mmbtu/year]']
    
    png_dict = {'population':'population',
    'generation_total [mmbtu/year]':'total',
    'generation_diesel [mmbtu/year]':'diesel',
    'generation_hydro [mmbtu/year]':'hydro',
    'generation_natural_gas [mmbtu/year]':'natural gas',
    'generation_wind [mmbtu/year]':'wind',
    'generation_solar [mmbtu/year]':'solar',
    'generation_biomass [mmbtu/year]':'biomass'}
    
    temp = []
    for i in png_list:
        if  all(gen_fc[i] == 0):
            continue
        temp.append(i)
    png_list = temp
    
    df2 = gen_fc[png_list]
    plot_name = name + ' Generation Forecast'
    
    fig, ax = plot.setup_fig(plot_name ,'years','population')
    ax1 = plot.add_yaxis(fig,'Generation MMBtu')
    
    plot.plot_dataframe(ax1,df2,ax,['population'],png_dict)
    fig.subplots_adjust(right=.85)
    fig.subplots_adjust(left=.12)
    start = models[0].\
            fc.p_map[models[0].fc.p_map['population_qualifier'] == 'P'].index[0]
    plot.add_vertical_line(ax,start, 'forecasting starts' )


    plot.create_legend(fig,.20)
    if img_dir is None:
        img_dir = os.path.join(path,'images')
    plot.save(fig,os.path.join(img_dir,
                            name.replace(" ",'_') + "_generation_forecast.png"))
    plot.clear(fig)

    out_file = os.path.join(path,
                            name.replace(" ",'_') + "_generation_forecast.csv")
    fd = open(out_file, 'w')
    fd.write("# Generation forecast\n")
    fd.write("# projections start in " + str(int(last_idx+1)) + "\n")
    fd.close()
    gen_fc[order].to_csv(out_file, index_label="year", mode = 'a')   
    return gen_fc
    
    
def run (batch_file, suffix = "TS", img_dir= None, dev = False):
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
    stuff = run_batch(batch_file, suffix,img_dir)
    warnings.filterwarnings("default")
    return stuff
    
    
    
    
    
    
    
    
    
    
    
    
