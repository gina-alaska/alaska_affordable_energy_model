"""
run_command.py

    A commad for the cli to run the model
"""
import pycommand
from aaem import driver, __version__, __download_url__
from datetime import datetime
import os.path
import shutil
import sys

class RunCommand(pycommand.CommandBase):
    """
    run command class
    """
    usagestr = ('usage: run path_to_model_run '
                                    '[list_of_communities (with underscores)] ')
    optionList = (
           ('log', ('l', "<log_file>", "name/path of file to log outputs to")),
    )
    description = 'Run model for given communities. (default = all communities)'

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            print  "run needs a directory"
            return 0
        
        config = os.path.join(base,"config")
        if len(self.args[1:]) != 0:
            coms = self.args[1:]
        else:
            coms = [a for a in os.listdir(config) if '.' not in a]
        
        batch = {}
        for com in coms:
            batch[com] = os.path.join(config,com,com+"_driver.yaml")
        
        try:
            shutil.rmtree(os.path.join(base,'results'))
        except OSError:
            pass
        sout = sys.stdout
        
        
        if self.flags.log:
            sys.stdout  = open(self.flags.log, 'w')
        driver.run(batch, "")
        sys.stdout = sout
        
        fd = open(os.path.join(base, "version_metadata.txt"), 'r')
        lines = fd.read().split("\n")
        fd.close()
        fd = open(os.path.join(base, "version_metadata.txt"), 'w')
        fd.write(( "Code Version: "+ __version__ + "\n" 
                   "Code URL: "+ __download_url__ + "\n" 
                   "" + lines[1] +'\n'
                "Date Run: "+ datetime.strftime(datetime.now(),"%Y-%m-%d")+'\n'
                 ))
        fd.close()
