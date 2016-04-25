"""
setup_command.py

    A commad for the cli to setup the model
"""
import pycommand
import sys
import os.path
from aaem import driver
from pandas import read_csv
from default_cases import __DEV_COMS__
import cli_lib

class SetupCommand(pycommand.CommandBase):
    """
    setup command class
    """
    usagestr = 'usage: setup [options] data repo'
    optionList = (
           ('path', ('p', "<name>", "path to location to setup/run  model")),
           ('dev', ('d', False, "use only development communities")),
           #~ ('name', ('n', "<name>", "name of model")),
    )

    description = ('Set up directory for running AAEM Models\n\n'
                   'options: \n'
                   "  " + str([o[0] + ': ' + o[1][2] + '. Use: --' +\
                   o[0] + ' (-'+o[1][0]+') ' +  (o[1][1] if o[1][1] else "")  +\
                   '' for o in optionList]).replace('[','').\
                   replace(']','').replace(',','\n ')
            )

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]):
            repo = os.path.abspath(self.args[0])
        else:
            print  "Setup Error: please provide a path to the aaem data repo"
            return 0

        path = os.getcwd()
        if self.flags.path:
            path = os.path.abspath(self.flags.path)

        #add this later?
        name = ""
        #~ if self.flags.name:
            #~ name = '_' + self.flags.name




        model_root = os.path.join(path,"model" + name)
        #~ print model_root
        try:
            os.makedirs(os.path.join(model_root))
        except OSError:
            print "Setup Error: model already setup at provided location"
            return 0
        try:
            os.makedirs(os.path.join(model_root, 'setup',"raw_data"))
        except OSError:
            pass
        #~ try:
            #~ os.makedirs(os.path.join(model_root, 'setup',"input_data"))
        #~ except OSError:
            #~ pass
        #~ try:
            #~ os.makedirs(os.path.join(model_root, 'run_init', "config"))
        #~ except OSError:
            #~ pass
        #~ try:
            #~ os.makedirs(os.path.join(model_root, 'run_init', "results"))
        #~ except OSError:
            #~ pass

        raw = os.path.join(model_root, 'setup', "raw_data")
        cli_lib.copy_model_data (repo, raw)
        #avaliable coms

        if self.flags.dev:
            coms = __DEV_COMS__
            full = False
        else:
            coms = read_csv(os.path.join(raw,'community_list.csv'),
                         comment="#",index_col=0).Community.tolist()
            full = True

        img_dir = os.path.join(model_root,'run_init','results','__images')

        print "Setting up..."
        config = driver.setup(coms, raw, model_root, setup_intertie = full)
        print "Running ..."
        coms = driver.run(config, "",img_dir )
        
        base = os.path.join(model_root,'run_init')
        cli_lib.generate_summaries (coms, base)




if __name__ == '__main__':
    # Shortcut for reading from sys.argv[1:] and sys.exit(status)
    pycommand.run_and_exit(SetupCommand)
