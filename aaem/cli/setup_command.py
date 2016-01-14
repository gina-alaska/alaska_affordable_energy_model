import pycommand
import sys
import os.path
from aaem import driver

class SetupCommand(pycommand.CommandBase):
    usagestr = 'usage: setup [directory]'
    description = 'Set up directory for running AAEM Models'

    optionList = (
           ('path', ('n', "<name>", "name of model")),
        #~ ('name', ('n', "<name>", "name of model")),
    )

    def run(self):
        
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

    coms = ["Bethel","Craig","Dillingham","Haines","Manley Hot Springs","Nome",
            "Sand Point","Sitka","Tok","Yakutat","Valdez"]
        driver.setup_multi([coms])

if __name__ == '__main__':
    # Shortcut for reading from sys.argv[1:] and sys.exit(status)
    pycommand.run_and_exit(SetupCommand)
