"""
refresh_command.py

    A commad for the cli to refresh the data
"""
import pycommand
import sys
import os.path
import shutil
import zipfile
from aaem import  __version__
from datetime import datetime
from pandas import read_csv
from default_cases import __DEV_COMS__
import cli_lib

from aaem import driver_2 as driver

class RefreshCommand(pycommand.CommandBase):
    """
    refesh command class
    refesh command class
    """
    usagestr = 'usage: refresh model_dir data_repo [tag]'
    optionList = (
           ('dev', ('d', False, "use only development communities")),
           ('force',('f', False, "force refresh of existing directory")),
    )

    description = ('Refresh the data from the data repo\n\n'
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
            model_root = os.path.abspath(self.args[0])
        else:
            print "Refresh Error: please provide a path to the model"
            return 0
        if self.args and os.path.exists(self.args[1]):
            repo = os.path.abspath(self.args[1])
        else:
            print "Refresh Error: please provide a path to the aaem data repo"
            return 0

        if self.args:
            try:
                tag = self.args[2]
            except IndexError:
                tag = None
           
        force = True
        if self.flags.force is None:
            force = False
     
        if self.flags.dev:
            coms = __DEV_COMS__
            interties = False
        else:
            coms = read_csv(os.path.join(repo,'community_list.csv'),
                         comment="#",index_col=0).Community.tolist()
    
        my_setup = driver.Setup(model_root, sorted(coms), repo, tag)
        if not my_setup.setup(force):
            pth = os.path.join(model_root, my_setup.tag)
            print "Refresh Error: " + pth + \
                    " exists. Use force flag (-f) to overwrite"
        
