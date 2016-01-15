import pycommand
import sys
import os.path
import shutil
from aaem import driver

class SetupCommand(pycommand.CommandBase):
    usagestr = 'usage: setup [data repo]'
    description = 'Set up directory for running AAEM Models'
    
    

    optionList = (
           ('path', ('p', "<name>", "path to create model structure")),
           #~ ('src', ('s', "<path to data>", "path to data repo")),
        #~ ('name', ('n', "<name>", "name of model")),
    )

    def run(self):
        print self.args
        if self.args and os.path.exists(self.args[0]):
            repo = os.path.abspath(self.args[0])
        else:
            print  "setup: please provide a path to the data repo"
            return 0
        #~ if not self.flags.path:
            #~ print  "setup: src (-s) is a required flag "
            #~ return 0
        #~ print('Python version ' + sys.version.split()[0]))
        
        path = os.getcwd()
        if self.flags.path:
            path = os.path.abspath(self.flags.path)
            
        name = ""
        #~ if self.flags.name:
            #~ name = '_' + self.flags.name
            
        
        
        
        try:
            model_root = os.path.join(path,"model" + name)
            os.makedirs(os.path.join(model_root, "raw_data"))
            os.makedirs(os.path.join(model_root, "input_data"))
            os.makedirs(os.path.join(model_root, "config"))
            os.makedirs(os.path.join(model_root, "results"))
        except OSError:
            pass
            
        raw = os.path.join(model_root, "raw_data")
        shutil.copy(os.path.join(repo, 
                        "2013-add-power-cost-equalization-pce-data.csv"), raw)
        shutil.copy(os.path.join(repo, "com_building_estimates.csv"), raw)
        shutil.copy(os.path.join(repo, "com_num_buildings.csv"), raw)
        shutil.copy(os.path.join(repo, "cpi.csv"), raw)
        shutil.copy(os.path.join(repo, "diesel_fuel_prices.csv"), raw)
        shutil.copy(os.path.join(repo, "eia_generation.csv"), raw)
        shutil.copy(os.path.join(repo, "eia_sales.csv"), raw)
        shutil.copy(os.path.join(repo, "hdd.csv"), raw)
        shutil.copy(os.path.join(repo, "heating_fuel_premium.csv"), raw)
        shutil.copy(os.path.join(repo, "interties.csv"), raw)
        shutil.copy(os.path.join(repo, "non_res_buildings.csv"), raw)
        shutil.copy(os.path.join(repo, "population.csv"), raw)
        shutil.copy(os.path.join(repo, "purchased_power_lib.csv"), raw)
        shutil.copy(os.path.join(repo, "res_fuel_source.csv"), raw)
        shutil.copy(os.path.join(repo, "res_model_data.csv"), raw)
        shutil.copy(os.path.join(repo, "valdez_kwh_consumption.csv"), raw)
        shutil.copy(os.path.join(repo, "ww_assumptions.csv"), raw)
        shutil.copy(os.path.join(repo, "ww_data.csv"), raw)

        coms = ["Bethel","Craig","Dillingham","Haines","Manley Hot Springs",
                "Nome","Sand Point","Sitka","Tok","Yakutat","Valdez"]
        
        driver.setup(coms, raw, model_root)

if __name__ == '__main__':
    # Shortcut for reading from sys.argv[1:] and sys.exit(status)
    pycommand.run_and_exit(SetupCommand)
