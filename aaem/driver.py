"""
driver.py

    will run the model
"""
from aaem import summaries, __version__, __download_url__
from aaem.components import comp_lib, comp_order
from community_data import CommunityData
from forecast import Forecast
from diagnostics import diagnostics
from preprocessor2 import Preprocessor,  PreprocessorError
#~ import defaults

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
    
from pandas import read_csv


default_scalers = {'diesel price': 1.0,
                   'diesel price adder': 0.0,
                  'capital costs': 1.0,
                  'kWh consumption': 1.0
                  }

class Driver (object):
    """ 
    Driver for the AAEM.
    
    Invariants:
        these variables should not change after intitilazation 
            self.model_root: is the model root path
            self.inputs_dir: is the default inputs directory
            self.config_dir: is the default confing directory
            self.global_config: is the default global config directory
            self.comp_lib: is a dictionay of components
            self.comp_order: list of the order of components to run
    """
    def __init__ (self, model_root):
        """ 
        set up driver 
        
        input:
            model_root: path to model root <string>
        
        output:
            none
        
        preconditions:
            none
       
        post:
            self.model_root: is the model root path
            self.inputs_dir: is the default inputs directory
            self.config_dir: is the default confing directory
            self.global_config: is the default global config directory
            self.comp_lib: is a dictionay of components
            self.comp_order: list of the order of components to run
        """
        self.model_root = model_root
        
        # default locations
        self.config_dir = os.path.join(model_root, 'config')
        
        self.global_config = os.path.join(model_root, 
                                            'config', '__global_config.yaml')
        ### MOVE TO PROCESSOR?? SCALERS??
        self.constuction_multipliers  = os.path.join(model_root, 'config', 
                                            '__regional_multipliers.yaml')
                                            
        self.comp_lib = comp_lib
        self.comp_order = comp_order
        
    def get_prereqs(self, comp_name):
        """
        get the prerequisits for a component
        
        inputs:
            comp_name: component name <string>
            
        outputs:
            returns list of prerequsite components
            
        preconditions:
            None
        
        postconditions:
            None
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
        get a component class
        
        inputs:
            comp_name: component name <string>
            
        outputs:
            returns a component class
            
        preconditions:
            None
        
        postconditions:
            None
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
        
    def setup_community (self, community_config, global_config, i_dir = None,
                          scalers = None):
        """
        
        """
        diag = diagnostics()
            
        if i_dir is None:
            com_dir = community.replace(' ','_').split('+')[0]
            i_dir = os.path.join(self.inputs_dir, com_dir) 

        try:
            cd = CommunityData( community_config,
                                global_config,
                                diag,
                                scalers)
        except IOError as e:
            raise RuntimeError, \
                ("A Fatal Error Has occurred, ("+ str(e) +")")
        try:
            fc = Forecast(cd, diag, scalers)
        except RuntimeError as e:
            raise RuntimeError, \
                    ("A Fatal Error Has occurred, ("+ str(e) +")")
        
        return cd, fc, diag
        
    def run_components (self, cd, fc, diag, scalers):
        """
        run enabled components
        
        intputs:
            cd: An initilized aaem.CommunityData object <aaem.CommunityData>
            fc: An initilized aaem.Forecast object <aaem.Forecast>
            diag: An initilized aaem.Diagnostis object <aaem.Diagnostics>
            cd, fc, and diag, should be for the same community
        
        outputs:
            returns comps_used, a dictionary of excuted components
        
        preconditions:
            see class invariants
            
        post:
            none
            
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
            component.run(scalers)
            ## faster to add this here than in each run func
            component.calc_internal_rate_of_return()
            
            comps_used[comp] = component
        return comps_used
    
        
    def save_components_output (self, comps_used, community, tag = ''):
        """
        save the output from each component
        
        inputs:
            comps_used: a dictionary of excuted components <dictionary>
            community: community or 'name' <string>
            tag: (optional) tag for results dir <string>
            
        outputs:
            saves components as .csv files
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'),
                                            "component_outputs/")
        #~ print directory
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
        save the forecast output
        
        inputs:
            fc: excuted forecast object <aaem.Forecast>
            community: community or 'name' <string>
            img_dir: directory to save plots <strings>
            plot: (optional, default False)boolean to plot <bool>
            tag: (optional) tag for results dir <string>
            
        outputs:
            saves forecast as .csv files, and plots, if plot == True
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'))
                                            
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
        fc.save_forecast(directory, img_dir, plot)
    
    def save_input_files (self, cd, community, tag = ''):
        """ 
        save the input files (confing yaml)
        
        inputs:
            cd: excuted community data object <aaem.CommunityData>
            community: community or 'name' <string>
            tag: (optional) tag for results dir <string>
            
        outputs:
            saves config used as a yaml file
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'))
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
        cd.save_model_inputs(os.path.join(directory,"config_used.yaml"))
    
    def save_diagnostics (self, diag, community, tag = ''):
        """ 
        save the diagnostic
        
        inputs:
            diag: excuted diagnostics object <aaem.Diagnostics>
            community: community or 'name' <string>
            tag: (optional) tag for results dir <string>
            
        outputs:
            saves diagnostic as .csv files
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag,
                                            community.replace(' ','_'))
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
                                        
        diag.save_messages(os.path.join(directory, 
                    community.replace(" ","_") + "_runtime_diagnostics.csv"))
                    
    def store_results (self, name, comps_used, tag = '', overwrite = False):
        """
        store results in binary pickle file
        
        inputs:
            name: community name or assigned 'name' <string>
            comps_used: a dictionary of excuted components <dictionary>
            tag: (optional) tag for results dir <string>
            overwrite: (optional, default: False) if true overwrite the 
                .pkl file <bool>
            
        outputs:
            saves binary output
            
        preconditions:
            see invariants
            
        postconditions:
            None
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
        """
            load a set of binary results from a piclkle file in the results 
        directory
        
        inputs:
            tag: (optional) tag for results dir <string>
            
        outputs:
            returns results as a dictionart of communities
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
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
                    i_dir = None, c_config = None, 
                    g_config = None, c_mult = None,
                    tag = '', img_dir = None, plot = False,
                    scalers = None):
        """
        run the model for a community
        
        inputs:
            community: the community <string>
            name: (optional, default: community) the assinged name for 
                the run <string>
            i_dir: (optional, default: none) alternate path to inputs 
                directory <string> 
            c_config: (optional, default: none) alternate community config 
                file <string>
            g_config: (optional, default: none) alternat global confing 
                file <string>
            tag: (optional) tag for results dir <string>
            img_dir: directory to save plots <strings>
            plot: (optional, default False)boolean to plot <bool>
            
        outputs:
            the model is run for a community/project/assigned 'name'
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if scalers is None:
            scalers = default_scalers
        
        if name is None:
            name = community
        
        temp = tag
        if img_dir is None:
            if temp != '':
                temp = '_' + tag
            img_dir = os.path.join(self.model_root, 'results' + temp, 'plots')
        
        cd, fc, diag = self.setup_community(community, i_dir, c_config, 
                                                    g_config, c_mult, scalers)
        
        comps_used = self.run_components(cd, fc, diag, scalers)
        
        self.save_components_output(comps_used, name, tag)
        self.save_forecast_output(fc, name, img_dir, plot, tag)
        self.save_input_files(cd, name, tag )
        self.save_diagnostics(diag, name, tag) 
        
        comps_used['community data'] = cd
        comps_used['forecast'] = fc
        self.store_results(name, comps_used, tag)
        
    def run_many (self, communities):
        """
        run a list of communites using default options
        
        inputs:
            communities: a list of communities <list>
        """
        for c in communities:
            self.run(c)
            
    def run_script(self):
        """
        TODO move code to run a script from cli
        """
        pass
        
            
    def save_metadata (self, tag = ""):
        """
        save model metadata
        
        inputs:
            tag: (optional) tag for results dir <string>
            
        outputs:
            saves version_metadata.txt
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
        
        with open(os.path.join(directory, "version_metadata.txt"), 'w') as fd:
             ts = datetime.strftime(datetime.now(), "%Y-%m-%d")
             fd.write(("Code Version: " + __version__ + "\n" 
                       "Code URL: " + __download_url__ + "\n" 
                       "Date Run: " + ts + '\n' ))

            
    def save_summaries (self, tag = ''):
        """
            save the summaries for the communities in a results directories 
        binary results file
        
        inputs:
            tag: (optional) tag for results dir <string>
            
        outputs:
            sumamry files are saved
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        res = self.load_results(tag)
        
        if tag != '':
            tag = '_' + tag
        directory = os.path.join(self.model_root, 'results' + tag)
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
        summaries.village_log(res,directory)
        summaries.building_log(res,directory)
        summaries.fuel_oil_log(res,directory)
        summaries.forecast_comparison_log(res,directory)
        summaries.electric_price_summary(res,directory)
        summaries.call_comp_summaries(res,directory)
        
        
    


class Setup (object):
    """
    setup the structure needed to run the model
    
    class invariants:
        self.model_root: is the model root path <string>
        self.communities: list of communities to setup <string>
        self.data_repo: path data repo <string>
        self.tag: tag used a the directory to setup the model in 
            model_root <string>
    """
    
    def __init__ (self, model_root, data_dir, communities = None, tag = None):
        """
        initilizer 
        
        inputs:
            model_root: model root path <string>
            communities: list of communities to setup <string>
            data_repo: path to data repo <sting>
            tag: (optional) tag to use as self.tag setup sub directory,
                if not provided self.tag will be m<version>_d<version> <string> 
            
        postconditions:
            see invatiants
        """
        self.model_root = model_root
        self.communities = communities
        self.data_dir = data_dir
        
        self.tag = tag
        if tag is None:
            self.tag = self.make_version_tag()
        self.diagnostics = diagnostics()
                
                
    def make_version_tag (self):
        """
        generate a version tag
        
        precondition:
            see invariants
            'VERSION' file must exist in repo
            
        outputs
            returns tag
        """
        data_version_file = os.path.join(self.data_dir, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
            ver = 'm' +  __version__  + '_d' + ver
        return ver
        
    def setup_directories (self):
        """ 
        setup the directories
        
        preconditions:
            see invariats
            
        postconditions:
            config and input_files are removed and then
            config and input_files directories are created.
        """
        setup_path = os.path.join(self.model_root, self.tag)
    
        try:
            shutil.rmtree(os.path.join(setup_path, "config"))
        except OSError:
            pass
        
        os.makedirs(os.path.join(setup_path, "config"))
            
    #~ def setup_community_configs (self, coms = None):
        #~ """
        #~ set up the conigureation files
        
        #~ inputs:
            #~ coms: (optional) alterante of communites to setup should be a 
                #~ subset of self.communities
        
        #~ post conditions:
            #~ saves a configuration .yaml for each community/ projcet in coms or 
        #~ self.communities
        #~ """
        #~ config_path = os.path.join(self.model_root, self.tag, 'config')
        #~ if coms is None:
            #~ coms = self.communities
        
        #~ for c in coms:
            #~ config = {'community':{'name': c,
                                   #~ 'model financial': True,},
                        #~ }
            #~ comments = {'community':{'name': 'name of community/project',
                                     #~ 'model financial': 'Model Finances?',},
               
                        #~ }
            #~ north_slope = ["Barrow", "Nuiqsut"] 
            #~ if c.split('+')[0] in north_slope or c.split('_')[0] in north_slope:
                #~ config['community']['natural gas price'] = 3
                #~ config['community']['natural gas used'] = True
                #~ comments['community']['natural gas price'] = 'LNG price $/gal'
                #~ comments['community']['natural gas used'] = \
                                                        #~ 'LNG used in community'
            
            #~ config_file = os.path.join(config_path, 
                                #~ c.replace(' ','_') + '_config.yaml')
            #~ header = 'community data for ' + c 
            #~ write_config_file(config_file, config, comments, 
                                            #~ s_order = ['community',],
                                            #~ i_orders = {'community':['name',
                                                        #~ 'model financial',
                                                        #~ 'natural gas used',
                                                        #~ 'natural gas price']},
                                            #~ header = header)
            
    def setup_community_list (self):
        """
        create the community list file from the repo
        
        preconditions:
            see invariants, community_list.csv sould exist in data repo
            
        postcondition:
            '__community_list.csv' saved in config directory
        """
        config_path = os.path.join(self.model_root, self.tag, 'config', 
                                                    '__community_list.csv')
        src_path = os.path.join(self.data_dir, 'community_list.csv')
        shutil.copy(src_path, config_path)
        
    #~ def setup_goals (self):
        #~ """
        #~ create the community list file from the repo
        
        #~ preconditions:
            #~ see invariants, community_list.csv sould exist in data repo
            
        #~ postcondition:
            #~ '__community_list.csv' saved in config directory
        #~ """
        #~ config_path = os.path.join(self.model_root, self.tag, 'input_files', 
                                                    #~ '__goals_community.csv')
        #~ src_path = os.path.join(self.data_repo, 'goals_community.csv')
        #~ shutil.copy(src_path, config_path)
        
        #~ config_path = os.path.join(self.model_root, self.tag, 'input_files', 
                                                    #~ '__goals_regional.csv')
        #~ src_path = os.path.join(self.data_repo, 'goals_regional.csv')
        #~ shutil.copy(src_path, config_path)
        
    #~ def setup_construction_multipliers (self):
        #~ """
        #~ create the construction multipliers file from the repo
        
        #~ preconditions:
            #~ see invariants, construction multipliers.yaml sould exist in 
        #~ data repo
            
        #~ postcondition:
            #~ '__construction multipliers.yaml' saved in config directory
        #~ """
        #~ config_path = os.path.join(self.model_root, self.tag, 'config', 
                                              #~ '__regional_multipliers.yaml')
        #~ src_path = os.path.join(self.data_repo, 'regional_multipliers.yaml')
        #~ shutil.copy(src_path, config_path)

    #~ def setup_global_config (self):
        #~ """
        #~ setup global config
        
        #~ preconditions:
            #~ see invariants
            
        #~ postcondition:
            #~ default '__global_config.yaml' saved in config directory
        #~ """
        #~ config_path = os.path.join(self.model_root, self.tag, 'config', 
                                                    #~ "__global_config.yaml")
        #~ with open(config_path, 'w') as def_file:
            #~ def_file.write(yaml.dump(defaults.build_setup_defaults(comp_lib),
                                                #~ default_flow_style = False))
            
    #~ def setup_input_files (self):
        #~ """
        #~ setup the input files, preprocessing the data
        
        #~ preconditions:
            #~ see invariants
            
        #~ postconditons:
            #~ sets up input files, and metadata
            
        #~ output:
            #~ returns the list of ids
        #~ """
        #~ input_path = os.path.join(self.model_root,self.tag,"input_files")
        
        #~ ids = self.preprocess_input_files(input_path)
        #~ self.move_input_files_diagnostics(input_path)
        #~ self.write_input_files_metadata(input_path)
        #~ self.archive_input_files_raw_data (input_path)
        #~ return ids
        
    #~ def preprocess_input_files (self, input_path):
        #~ """
        #~ preprocess input files
        
        #~ inputs:
            #~ input_path: path to preprocess the data into <string>
            
        #~ preconditions:
            #~ see invatiants
            
        #~ outputs:
            #~ returns ids of preprocessed communities/projects including interies
        #~ """
        #~ all_ids = []
        #~ for c in self.communities:
            #~ it_batch = {}
            #~ ids = preprocess(self.data_repo, input_path, c, dev = True)
            #~ all_ids += ids
            
        #~ return all_ids
            
    #~ def move_input_files_diagnostics (self, input_path):
        #~ """
        #~ move the input file diagnostics to a '__diagnostic_files' sub directory
        
        #~ inputs:
            #~ input_path: path to preprocess the data into <string>
        
        #~ postconditions:
            #~ move the input file diagnostics
        #~ """
        #~ diag_path = os.path.join(input_path, '__diagnostic_files')
        #~ try:
            #~ os.makedirs(diag_path)
        #~ except OSError:
            #~ pass
        #~ for diagf in [f for f in os.listdir(input_path) if '.csv' in f] : 
            #~ os.rename(os.path.join(input_path,diagf),
                        #~ os.path.join(diag_path,diagf))
          
    #~ def write_input_files_metadata (self, input_path):
        #~ """ 
        #~ write data metadata
        
        #~ inputs:
            #~ input_path: path to inputs directory <string>
            
        #~ outputs:
            #~ saves 'input_files_metadata.yaml' in "__metadata" subdirectory
        #~ """
        #~ data_version_file = os.path.join(self.data_repo, 'VERSION')
        #~ with open(data_version_file, 'r') as fd:
            #~ ver = fd.read().replace("\n", "")
            
        #~ md_dir = os.path.join(input_path, "__metadata")
        #~ try:
            #~ os.makedirs(md_dir)
        #~ except OSError:
            #~ pass
        #~ m = 'w'
        #~ with open(os.path.join(md_dir, 'input_files_metadata.yaml'), m) as meta:
            #~ meta.write(yaml.dump({'upadted': datetime.strftime(datetime.now(),
                                                        #~ "%Y-%m-%d %H:%M:%S"),
                                  #~ 'data version': ver},
                                  #~ default_flow_style = False))
                                  
    #~ def archive_input_files_raw_data (self, input_path):
        #~ """
        #~ saves an archive of the raw data in the meta dat folder
        
        #~ inputs:
            #~ input_path: path to inputs directory<string>
            
        #~ outputs:
            #~ saves in "raw_data.zip" in "__metadata" subdirectory
        #~ """
        #~ data_version_file = os.path.join(self.data_repo, 'VERSION')
        #~ with open(data_version_file, 'r') as fd:
            #~ ver = fd.read().replace("\n", "")
    
        #~ md_dir = os.path.join(input_path, "__metadata")
        #~ try:
            #~ os.makedirs(md_dir)
        #~ except OSError:
            #~ pass
        #~ z = zipfile.ZipFile(os.path.join(md_dir, "raw_data.zip"),"w")
        #~ for raw in [f for f in os.listdir(self.data_repo) if '.csv' in f]:
            #~ z.write(os.path.join(self.data_repo,raw), raw)
        #~ z.write(os.path.join(data_version_file), 'VERSION')
    def load_communities (self):
        """ Function doc """
        data = read_csv(os.path.join(self.model_root, self.tag, 'config', 
                                                    '__community_list.csv'))
        
        self.communities = [c for c in data['Community'].values]
        
    def setup (self, force = False):
        """
        run the setup functionality
        
        inputs:
            force: (optional) overwrirte existing files <boolean>
            
        outputs:
            model structure is setup
        """
        setup_path = os.path.join(self.model_root, self.tag)
        if os.path.exists(setup_path) and force == False:
            return False
            
        
        self.setup_directories()
        self.setup_community_list()
        
        if self.communities is None:
            self.load_communities()
        
        for community in self.communities:
            f_path = os.path.join(self.model_root, self.tag, 'config')
            preprocessor = Preprocessor(community,
                self.data_dir, 
                diag = self.diagnostics, 
                process_intertie = False)
            self.diagnostics.add_note('Preprocessing ' + community, '---------')
            preprocessor.run()
            
            preprocessor.save_config(f_path)
            
            ## the intertie, if it exists
            try:
                preprocessor = Preprocessor(community,
                    self.data_dir, 
                    diag = self.diagnostics, 
                    process_intertie = True)
                self.diagnostics.add_note('Preprocessing ' + community,
                    '---------')
                preprocessor.run()
                preprocessor.save_config(f_path)
            except  PreprocessorError:
                pass
        
        #~ self.setup_global_config()
        #~ ids = self.setup_input_files()
        #~ self.setup_community_configs()
        
        #~ self.setup_construction_multipliers()
        #~ self.setup_goals()
        return True
        
        
#~ def write_config_file(path, config, comments, s_order = None, i_orders = None, 
                            #~ indent = '  ' , header = ''):
    #~ """
    #~ write a config yaml file
    
    #~ inputs:
        #~ path: filename to save file at <string>
        #~ config: dictionary of configs <dict>
        #~ comments: dictionary of comments <dict>
        #~ s_order: (optional) order of sections <list>
        #~ i_orders: (optional) order of items in sections <dict>
        #~ indent: (optional) indent spacing <sting>
        #~ header: (optional) header line <string>
        
    #~ outputs:
        #~ saves config .yaml file at path
    #~ """
    #~ defaults.save_config(path, config, comments, s_order, 
                                #~ i_orders, indent, header)
    
def script_validator (script_file):
    """
        validate a script(very basic), will raise a standard error if a problem 
    is found
    
    inputs:
        script file: a script file
    
    outputs:
        retuns a validated script to use to run the model
    """
    extns = ['yaml','yml']
    with open(script_file, 'r') as sf:
        script = yaml.load(sf)
    
    gcfg = script['global']['config']
    if not os.path.isfile(gcfg) and \
           not os.path.split(gcfg)[1].split('.')[1] in extns:
        raise StandardError, "golbal config not a yaml file"
    
    try:
        img_dir = script['global']['image directory']
    except KeyError:
        script['global']['image directory'] = None
        img_dir = None
    
    try:
        plot = script['global']['plot']
    except KeyError:
        script['global']['plot'] = False
        plot = False 
        
    try:
        res_tag = script['global']['results tag']
    except KeyError:
        script['global']['results tag'] = ''
        res_tag = '' 
        
    try:
        script['global']['construction multipliers']
    except KeyError:
        script['global']['construction multipliers'] = None
    
    errors = []
    for com in script['communities']:
        if not os.path.exists(com['input files']):
            errors.append(com['community'] + ': input files is not a directory')
        if not os.path.isfile(gcfg) and \
                not os.path.split(gcfg)[1].split('.')[1] in extns:
            errors.append(com['community'] + ': config not a yaml file')
        try:    
            com['name']
        except KeyError:
            com['name'] = None
            
        if com['name'] is None:
            com['name'] = com['community']
            
        try:
            com['scalers']
        except KeyError:
            com['scalers'] = default_scalers
            
        for scaler in default_scalers:
            try:
                com['scalers'][scaler]
            except KeyError:
                com['scalers'][scaler] = default_scalers[scaler]
        
    if len(errors) != 0:
        errs = '\n'.join(errors)
        raise StandardError, errs
    
    return script
        
    
    


    
    
    
    
