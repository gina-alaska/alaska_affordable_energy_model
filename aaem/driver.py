"""
driver.py

    will run the model
"""
from aaem import summaries, __version__, __download_url__
from aaem.components import comp_lib, comp_order
from community_data import CommunityData
from forecast import Forecast
from diagnostics import Diagnostics
from preprocessor import Preprocessor,  PreprocessorError
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

KEYS_FOR_GLOBAL = { 
    'community': [
        'model electricity',
        'model heating fuel',
        'model financial',
        'interest rate',
        'discount rate',
        'current year',
    ],
    'Residential Energy Efficiency': [
        'enabled',
        'lifetime',
        'min kWh per household',
        'average refit cost',
    ],
    'Non-residential Energy Efficiency': [
        'enabled',
        'lifetime',
        'average refit cost', 
        'cohort savings percent',
        'heating percent',
        'waste oil cost percent'
    ],
    'Water and Wastewater Efficiency':[
        'enabled',
        'lifetime',
        'audit cost',
        'average refit cost',
        'electricity refit reduction',
        'heating fuel refit reduction',
        'heat recovery multiplier',
        'heating cost percent',
    ],
    'Wind Power':[
        'enabled',
        'lifetime',
        'average load limit',
        'percent generation to offset',
    ],
    'Solar Power':[
        'enabled',
        'lifetime',
        'average load limit',
        'percent generation to offset',
        'percent solar degradation',
        'cost per kW',
        'percent o&m',
    ],
    'Biomass for Heat (Cordwood)':[
        'enabled',
        'lifetime',
        'cost per btu/hrs',
        'o&m per year',
        'energy density',
        'hours of storage for peak',
        'percent at max output',
        'cordwood system efficiency',
        'hours operation per cord',
        'operation cost per hour',
        'boiler assumed output',
    ],
    'Biomass for Heat (Pellet)':[
        'enabled',
        'lifetime',
        'cost per btu/hrs',
        'o&m per year',
        'energy density',
        'pellet efficiency',
        'default pellet price',
    ],
    'Residential ASHP':[
        'enabled',
        'lifetime',
        'btu/hrs',
        'cost per btu/hrs',
        'o&m per year'
    ],
    'Non-Residential ASHP':[
        'enabled',
        'lifetime',
        'btu/hrs',
        'cost per btu/hrs',
        'o&m per year',
    ],
    'Hydropower':[
        'enabled',
        'lifetime',
        'percent o&m',
        'percent heat recovered',
    ],
    'Transmission and Interties':[
        'enabled',
        'lifetime',
        'transmission loss per mile',
        'percent o&m',
        'heat recovery o&m',
        'est. intertie cost per mile',
        'diesel generator o&m',
    ],
    'Heat Recovery':[
        'enabled',
        'lifetime',
        'estimate pipe distance',
        'estimate pipe cost/ft',
        'estimate buildings to heat',
        'heating conversion efficiency',
        'percent heat recovered',
        'estimate cost/building',
        'o&m per year',
    ],
    'Diesel Efficiency':[
        'enabled',
        'lifetime',
        'efficiency improvment',
        'o&m costs'
    ],
}


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
            self.comp_lib: is a dictionary of components
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
            self.comp_lib: is a dictionary of components
            self.comp_order: list of the order of components to run
        """
        self.model_root = model_root
        
        # default locations
        #~ self.config_dir = os.path.join(model_root, 'config')
        
        #~ self.global_config = os.path.join(model_root, 
                                            #~ 'config', '__global_config.yaml')
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

    def save_components_output (self, comps_used, community,
        forecast, tag = '', alt_name = None):
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

        if alt_name is None:
            save_name = community.replace(' ','_')
        else:
            save_name = alt_name.replace(' ','_')
            
        directory = os.path.join(
            self.model_root, 'results' + tag, save_name)
        #~ print directory
        
        
    
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
            
        summaries.community_forcast_summaries(
            community, comps_used, forecast, directory)
            
        directory = os.path.join(directory, "component_outputs/")
        #~ print directory
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
        
            
        for comp in comps_used:
            #~ continue
            try:
                comps_used[comp].save_csv_outputs(directory)
                comps_used[comp].save_additional_output(directory)
            except:
                pass
    
    def save_input_files (self, cd, community, tag = '', alt_name = None):
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
        
        if alt_name is None:
            save_name = community.replace(' ','_')
        else:
            save_name = alt_name.replace(' ','_')
            
        directory = os.path.join(self.model_root, 'results' + tag, save_name)
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
        cd.save(os.path.join(directory,"config_used.yaml"))
    
    def save_diagnostics (self, diag, community, tag = '', alt_name = None):
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
        
        if alt_name is None:
            save_name = community.replace(' ','_')
        else:
            save_name = alt_name.replace(' ','_')
            
        directory = os.path.join(self.model_root, 'results' + tag, save_name)
        try:
            os.makedirs(os.path.join(directory))
        except OSError:
            pass
                                        
        diag.save_messages(os.path.join(directory, 
                    community.replace(" ","_") + "_runtime_diagnostics.csv"))
                    
    def store_results (self, comps_used, tag = '',
        overwrite = False, name = None):
        """
        store results in binary pickle file
        
        inputs:
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
        
        if name == None:
            name = comps_used['community data'].get_item('community', 'file id')

        picklename = os.path.join(directory,'binary_results.pkl')
        if overwrite:
            mode = 'rb'
        else:
            mode = 'ab'
        #~ print picklename
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
        
    def run (self, community_config, global_config = None, 
        tag = '', scalers = None, alt_save_name = None):
        """
        run the model for a community
        
        inputs:
            community: the community <string>
            c_config: (optional, default: none) alternate community config 
                file <string>
            g_config: (optional, default: none) alternat global confing 
                file <string>
            tag: (optional) tag for results dir <string>
            
        outputs:
            the model is run for a community/project/assigned 'name'
            
        preconditions:
            see invariants
            
        postconditions:
            None
        """
        #~ print community_config
      
        if scalers is None:
            scalers = default_scalers
        
        #~ if name is None:
            #~ name = community
        
        temp = tag
        #~ if img_dir is None:
            #~ if temp != '':
                #~ temp = '_' + tag
            #~ img_dir = os.path.join(self.model_root, 'results' + temp, 'plots')
        
        #~ cd, fc, diag = self.setup_community(community, i_dir, c_config, 
                                                    #~ g_config, c_mult, scalers)
                                                    
        diagnostics = Diagnostics()
        community_data = CommunityData( 
            community_config, 
            global_config, 
            diagnostics,
            scalers
        )
        name = community_data.get_item('community', 'file id')
        #~ print name
        forecast = Forecast(community_data, diagnostics, scalers)
                                                    
        
        comps_used = self.run_components(
            community_data,
            forecast,
            diagnostics,
            scalers
        )
        
        
        
        #~ name = community_data.get_item('community', 'file id')
        self.save_components_output(comps_used, name, forecast, tag, 
            alt_name=alt_save_name)
        #~ self.save_forecast_output(forecast, name, img_dir, plot, tag)
        self.save_input_files(community_data, name, tag, alt_name=alt_save_name)
        self.save_diagnostics(diagnostics, name, tag, alt_name=alt_save_name) 

        
        comps_used['community data'] = community_data
        comps_used['forecast'] = forecast
        
    
        #~ print name 
        #~ print 'rb', alt_save_name
        self.store_results(comps_used, tag, name=alt_save_name)
        
    def run_many (self, directory):
        """
        run a list of communities using default options
        
        inputs:
            communities: a list of communities <list>
        """
        
        communities = \
            [f for f in os.listdir( directory ) \
            if f.endswith('.yaml') or f.endswith('.yml')]
        for c in communities:
            try:
                self.run(os.path.join(directory,c))
            except (RuntimeError, IOError) as e:
                print '------------------------'
                print e
                msg = "RUN ERROR: "+ c + \
                                    " not a configured community/project"
                print msg
                print '------------------------'
            
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
        #~ print res
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
        self.diagnostics = Diagnostics()
                
                
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
          
    def write_preprocessor_metadata (self, save_path):
        """ 
        write data metadata
        
        inputs:
            input_path: path to inputs directory <string>
            
        outputs:
            saves 'input_files_metadata.yaml' in "__metadata" subdirectory
        """
        data_version_file = os.path.join(self.data_dir, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
            
        md_dir = os.path.join(save_path, "__metadata")
        try:
            os.makedirs(md_dir)
        except OSError:
            pass
        #~ try:
            #~ os.makedirs(os.path.join(md_dir,'diagnostic_files'))
        #~ except OSError:
            #~ pass    
        
        m = 'w'
        with open(
            os.path.join(md_dir, 'preprocessor_metadata.yaml'),
             m) as meta:
            meta.write(yaml.dump({'upadted': datetime.strftime(datetime.now(),
                                                        "%Y-%m-%d %H:%M:%S"),
                                  'data version': ver},
                                  default_flow_style = False))
                                  
        self.diagnostics.save_messages(os.path.join(md_dir, 'log.csv'))
                                  

        data_version_file = os.path.join(self.data_dir, 'VERSION')
        with open(data_version_file, 'r') as fd:
            ver = fd.read().replace("\n", "")
            
        z = zipfile.ZipFile(os.path.join(md_dir, "raw_data.zip"),"w")
        for raw in [f for f in os.listdir(self.data_dir) if '.csv' in f]:
            z.write(os.path.join(self.data_dir,raw), raw)
        z.write(os.path.join(data_version_file), 'VERSION')
        
        
    def load_communities (self):
        """ Function doc """
        data = read_csv(os.path.join(self.model_root, self.tag, 'config', 
                                                    '__community_list.csv'))
        
        self.communities = [c for c in data['Community'].values]
        
    def setup (self, force = False, ng_coms = [], make_globals = False):
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
        
        f_path = os.path.join(self.model_root, self.tag, 'config')
        for community in self.communities:
            #~ print community
            #~ f_path = os.path.join(self.model_root, self.tag, 'config')
            preprocessor = Preprocessor(community,
                self.data_dir, 
                diag = self.diagnostics, 
                process_intertie = False)
            self.diagnostics.add_note('Preprocessing ' + community, '---------')
            if community in ng_coms:
                preprocessor.run(show=True, ng_com=True)
            else:
                preprocessor.run(show=True)
            
            if  make_globals:
                keys_to_split = KEYS_FOR_GLOBAL
                preprocessor.save_config(f_path, keys_to_split)
                f_name = os.path.join(f_path, '__global_config.yaml')
                if not os.path.exists(f_name):
                    preprocessor.save_global_congfig(f_name, keys_to_split)
            else:
                preprocessor.save_config(f_path)
            ## the intertie, if it exists
            try:
                preprocessor = Preprocessor(community,
                    self.data_dir, 
                    diag = self.diagnostics, 
                    process_intertie = True)
                self.diagnostics.add_note('Preprocessing ' + community,
                    '---------')
                preprocessor.run(show=True)
                if  make_globals:
                    keys_to_split = KEYS_FOR_GLOBAL
                    preprocessor.save_config(f_path, keys_to_split)
                else:
                    preprocessor.save_config(f_path)
            except PreprocessorError:
                pass
        
        #~ self.setup_global_config()
        #~ ids = self.setup_input_files()
        #~ self.setup_community_configs()
        
        #~ self.setup_construction_multipliers()
        #~ self.setup_goals()
        self.write_preprocessor_metadata(f_path)
        return True
    
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
        
    try:
        root = script['global']['root']
    except KeyError:
        raise StandardError, "No root provided for model structure"
    
    try:
        gcfg = script['global']['global config']
        if not os.path.isfile(gcfg) and \
            not os.path.split(gcfg)[1].split('.')[1] in extns:
            raise StandardError, "golbal config not a yaml file"
    except KeyError:
        script['global']['global config'] = None
        
    if script['global']['global config'] is None:
        gc = os.path.join(root, 'config', '__global_config.yaml')
        if os.path.isfile(gc):
            script['global']['global config'] = gc 
        
    try:
        res_tag = script['global']['results tag']
    except KeyError:
        script['global']['results tag'] = ''
        res_tag = '' 
    
    errors = []
    all_coms = set()
    for com in script['communities']:
        community = com['community'].replace(' ','_')
        try:    
            com['ID']
        except KeyError:
            com['ID'] = None
            
        if com['ID'] is None:
            com['ID'] = com['community']
        
        if com['ID'] in all_coms:
            raise StandardError, "Community: " + com + ' appears more than' + \
                ' once in the script. Ensure that each time the community' + \
                ' appears in the script it has a unique ID feild' 
        
        all_coms.add(com['ID'])
        
        try:
            com['config']
        except KeyError:
            com['config'] = os.path.join(root, 'config', community + '.yaml')
        
        if not os.path.isfile(com['config']):  
            if os.path.isfile(os.path.join(root, 'config', community + '.yml')):
                com['config'] = os.path.join(root, 'config', community + '.yml')
            else:
                raise StandardError, com['config'] + ' is not a file'
                
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
    #~ print script
    return script
        
    
    


    
    
    
    
