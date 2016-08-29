"""
setup_command.py

    A commad for the cli to setup the model
"""
import pycommand
import sys
import os.path
import shutil
from pandas import read_csv
from default_cases import __DEV_COMS__
import cli_lib

from aaem import driver_2 as driver

class SetupCommand(pycommand.CommandBase):
    """
    setup command class
    """
    usagestr = \
        'usage: setup [options] location_to_setup data_repo [tag]'
    optionList = (
           
           ('dev', ('d', False, "use only development communities")),
           ('force',('f', False, "force overwrite of existing directories")),
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
        # argument setup
        if len(self.args) < 2 :
            msg = "SETUP ERROR: provide location to setup & the data repo"
            cli_lib.print_error_message(msg, SetupCommand.usagestr)
            return 0
        
        model_root = self.args[0]
    
        repo = os.path.abspath(self.args[1])
        
        if not os.path.exists(repo):
            msg = "SETUP ERROR: provided repo directory does not exist"
            cli_lib.print_error_message(msg, SetupCommand.usagestr)
            return 0
            
        try:
            tag = self.args[2]
        except IndexError:
            tag = None
        
        # option setup
        force = True
        if self.flags.force is None:
            force = False

        ## SET UP
        print repo
        try:
            if self.flags.dev:
                coms = __DEV_COMS__
            else:
                coms = read_csv(os.path.join(repo,'community_list.csv'), 
                                    comment="#",index_col=0).Community.tolist()
            print "Setting up ..."

            my_setup = driver.Setup(model_root, coms, repo, tag)
            if not my_setup.setup(force):
                pth = os.path.join(model_root, my_setup.tag)
                msg = "SETUP ERROR: " + pth + \
                        " exists. Use force flag (-f) to overwrite"
                cli_lib.print_error_message(msg, SetupCommand.usagestr)
                return
            
        except IOError:
            msg = "SETUP ERROR: provided repo has missing files"
            cli_lib.print_error_message(msg, SetupCommand.usagestr)
            return


        ## Generate inital results
        print "Running ..."
        
        base = os.path.join(model_root,my_setup.tag)
        try:
            shutil.rmtree(os.path.join(base,'results'))
        except OSError:
            pass
    
        my_driver = driver.Driver(base)
        for com in sorted(cli_lib.get_config_coms(base)):
            print com
            my_driver.run(com)
        my_driver.save_summaries()
        my_driver.save_metadata()





if __name__ == '__main__':
    # Shortcut for reading from sys.argv[1:] and sys.exit(status)
    pycommand.run_and_exit(SetupCommand)
