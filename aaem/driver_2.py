"""
driver.py

    will run the model
"""
from aaem import summaries, __version__, __download_url__
from aaem.components import comp_lib, comp_order
from community_data import CommunityData
from forecast import Forecast
from diagnostics import diagnostics
from preprocessor import preprocess
import defaults

import yaml
import os.path
from importlib import import_module
from datetime import datetime
import zipfile
import shutil
try:
    import cPickle as pickle
    #~ print "C Pickle"
except ImportError:
    import pickle


class Driver (object):
    """ 
    Driver for the AAEM.
    """
    def __init__ (self, model_root):
        """ 
        set up driver 
        
        pre:
            infile is an absolute path 
        post:
            model is ready to be run
        """
        self.model_root = model_root
        
        # default locations
        self.inputs_dir = os.path.join(model_root, 'input_files')
        self.config_dir = os.path.join(model_root, 'config')
        self.global_config = os.path.join(model_root, 
                                            'config', '__global_config.yaml')
                                            
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
        self.comp_lib = comp_lib
        self.comp_order = comp_order
        
    def get_prereqs(self, comp_name):
        """
        """
        try:
            return self.preq_lib[comp_name]
        except AttributeError:
            self.preq_lib = {}
        except KeyError:
            pass
            
        self.preq_lib[comp_name] = \
                    import_module("aaem.components." + comp_name).prereq_comps
        return self.preq_lib[comp_name]
    
    def get_component (self, comp_name):
        """
        import a component
        pre:
            comp name is the name of a component
        post:
            returns imported module
        """
        try:
            return self.imported_comps[comp_name]
        except AttributeError:
            self.imported_comps = {}
        except KeyError:
            pass
            
        self.imported_comps[comp_name] = \
                    import_module("aaem.components." + comp_name).component
        return self.imported_comps[comp_name]
        
    def setup_community (self, community, i_dir = None,
                                c_config = None, g_config = None):
        """ Function doc """
        diag = diagnostics()
        
        if c_config is None:
            c_config = os.path.join(self.config_dir,
                                community.replace(' ','_') + "_config.yaml")
        
        if g_config is None:
            g_config = self.global_config
            
        if i_dir is None:
            com_dir = community.replace(' ','_').split('+')[0]
            i_dir = os.path.join(self.inputs_dir, com_dir) 
            
        #~ try:
        cd = CommunityData(i_dir, c_config, g_config, diag)
        #~ except IOError as e:
            #~ raise RuntimeError, \
                #~ ("A Fatal Error Has occurred, ("+ str(e) +")")
        try:
            fc = Forecast(cd, diag)
        except RuntimeError as e:
            raise RuntimeError, \
                    ("A Fatal Error Has occurred, ("+ str(e) +")")
        
        return cd, fc, diag
        
    def run_components (self, cd, fc, diag):
        """
        run enabled components
        pre:
            self.comp_lib exists
        post:
            self.comps_used is a dictionary of the used components. 
        """
        comps_used = {}
        for comp in self.comp_order:
            if cd.get_item(comp, "enabled") == False:
                continue
                
            prereq = {}
            pr_list = self.get_prereqs(self.comp_lib[comp])
                
            for pr in pr_list:
                prereq[pr] = comps_used[pr]
                
            CompClass = self.get_component(self.comp_lib[comp])
            component = CompClass (cd, fc, diag, prereq)
            component.run()
            
            comps_used[comp] = component
        return comps_used
    
        
    def save_components_output (self, comps_used, community, tag = ''):
        """
        save the output from each component
        pre:
            self.comps_used should be a set of run components
        post:
            for each component in self.comps_used the electric, heating, and
        financial outputs are saved as csv files 
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'),
                                            "component_outputs/")
        
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
            
        for comp in comps_used:
            comps_used[comp].save_csv_outputs(directory)
            comps_used[comp].save_additional_output(directory)
    
    def save_forecast_output (self, fc, community, img_dir, 
                                                    plot = False, tag = ''):
        """
        save the forecast output:
        pre:
            forecast.save_forecast preconditions are met.
        post: 
            the forecast is saved as a csv file
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'))
        
        fc.save_forecast(directory, img_dir, plot)
    
    def save_input_files (self, cd, community, tag = ''):
        """ 
        save the config used
        pre:
            model needs to have been run
        post:
            the inputs used for each component are saved
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'))
        
        cd.save_model_inputs(os.path.join(directory,"config_used.yaml"))
    
    def save_diagnostics (self, diag, community, tag = ''):
        """ 
        save the diagnostics
        pre:
            directory is the location to save the file
        post:
            diagnostics file is saved
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'))
                                            
        diag.save_messages(os.path.join(directory, 
                    community.replace(" ","_") + "_runtime_diagnostics.csv"))
                    
    def store_results (self, name, comps_used, tag = '', overwrite = False):
        """
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        
        picklename = os.path.join(directory,'binary_results.pkl')
        if overwrite:
            mode = 'rb'
        else:
            mode = 'ab'
            
        with open(picklename, mode) as pkl:
             pickle.dump([name, comps_used], pkl, pickle.HIGHEST_PROTOCOL)
             
    def load_results (self, tag = ''):
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        results = {}
        picklename = os.path.join(directory,'binary_results.pkl')
        with open(picklename, 'rb') as pkl:
            while True:
                try:
                    temp = pickle.load(pkl)
                    key = temp[0]
                    i = 0
                    while key in results.keys():
                        key = key.split(' #')[0] + ' #' + str(i)
                        i += 1
                    
                    results[key] = temp[1]
                except:
                    break
        return results
        
    def run (self, community, name = None, 
                    i_dir = None, c_config = None, g_config = None,
                    tag = '', img_dir = None, plot = False):
        """
        model root ./model/m0.18.0... 
        """
        if name is None:
            name = community
        
        temp = tag
        if img_dir is None:
            if temp != '':
                temp = '_' + tag
            img_dir = os.path.join(self.model_root, 'results' + temp, 'plots')
        
        cd, fc, diag = self.setup_community(community, i_dir, 
                                                        c_config, g_config)
        comps_used = self.run_components(cd, fc, diag)
        
        self.save_components_output(comps_used, community)
        
        self.save_forecast_output(fc, community, img_dir, plot, tag)
        self.save_input_files(cd, community, tag )
        self.save_diagnostics(diag, community, tag) 
        
        comps_used['community data'] = cd
        comps_used['forecast'] = fc
        self.store_results(name, comps_used, tag)
        
    def run_many (self, communities):
        """ Function doc """
        for c in communities:
            self.run(c)
            
    def save_metadata (self, tag = ""):
        """ Function doc """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        
        with open(os.path.join(directory, "version_metadata.txt"), 'w') as fd:
             ts = datetime.strftime(datetime.now(), "%Y-%m-%d")
             fd.write(("Code Version: " + __version__ + "\n" 
                       "Code URL: " + __download_url__ + "\n" 
                       "Date Run: " + ts + '\n' ))

            
    def save_summaries (self, tag = ''):
        res = self.load_results(tag)
        
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        
        summaries.village_log(res,directory)
        summaries.building_log(res,directory)
        summaries.fuel_oil_log(res,directory)
        summaries.forecast_comparison_log(res,directory)
        summaries.electric_price_summary(res,directory)
        summaries.call_comp_summaries(res,directory)
        
        
    


class Setup (object):
    """ Class doc """
    
    def __init__ (self, model_root, communities, data_repo, tag = None):
        """ Class initialiser """
        self.model_root = model_root
        self.communities = communities
        self.data_repo = data_repo
        
        self.tag = tag
        if tag is None:
            self.tag = self.make_version_tag()
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
            shutil.rmtree(os.path.join(setup_path, "input_files"))
        except OSError:
            pass
        try:
            shutil.rmtree(os.path.join(setup_path, "config"))
        except OSError:
            pass
        
        os.makedirs(os.path.join(setup_path, "input_files"))
        os.makedirs(os.path.join(setup_path, "config"))
            
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
                                c.replace(' ','_') + '_config.yaml')
            header = 'community data for ' + c 
            write_config_file(config_file, config, comments, 
                                            s_order = ['community',],
                                            i_orders = {'community':['name',
                                                        'model financial',
                                                        'natural gas used',
                                                        'natural gas price']},
                                            header = header)
            
    def setup_community_list (self):
        config_path = os.path.join(self.model_root, self.tag, 'config', 
                                                    '__community_list.csv')
        src_path = os.path.join(self.data_repo, 'community_list.csv')
        
        
        shutil.copy(src_path, config_path)

    def setup_global_config (self):
        """ Function doc """
        config_path = os.path.join(self.model_root, self.tag, 'config', 
                                                    "__global_config.yaml")
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
            
        md_dir = os.path.join(input_path, "__metadata")
        try:
            os.makedirs(md_dir)
        except OSError:
            pass
        m = 'w'
        with open(os.path.join(md_dir, 'input_files_metadata.yaml'), m) as meta:
            meta.write(yaml.dump({'upadted': datetime.strftime(datetime.now(),
                                                        "%Y-%m-%d %H:%M:%S"),
                                  'data version': ver},
                                  default_flow_style = False))
                                  
    def archive_input_files_raw_data (self, input_path):
        """ """
        data_version_file = os.path.join(self.data_repo, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
    
        md_dir = os.path.join(input_path, "__metadata")
        try:
            os.makedirs(md_dir)
        except OSError:
            pass
        z = zipfile.ZipFile(os.path.join(md_dir, "raw_data.zip"),"w")
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
        self.setup_community_list()
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
    
    
            
    
    
    
    
    
