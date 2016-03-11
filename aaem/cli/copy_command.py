"""
run_command.py

    A commad for the cli to copy a model run
"""
import pycommand
import shutil
import os.path
from aaem import driver
from datetime import datetime

class CopyCommand(pycommand.CommandBase):
    """
    copy command class
    """
    usagestr = 'usage: copy [options] path_to_model_run_to_copy'
    description = 'set up a new model run based off an old one'
    
    optionList = (
           ('tag', ('t', "<name>", "tag for run directory")),
    )
    description = ('Set up a new model run based off an old one\n\n'
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
            base = os.path.abspath(self.args[0])
        else:
            print  "Copy Error: needs a existing run"
            return 0
    
        
        model_root = os.path.split(base)[0]
        
        if self.flags.tag:
            tag = self.flags.tag
        else:
            tag = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
        new = os.path.join(model_root, tag)
        
        try:
            shutil.copytree(os.path.join(base,"input_data"), 
                                                os.path.join(new,"input_data"))
            shutil.copytree(os.path.join(base,"config"), 
                                                os.path.join(new,"config"))
        except OSError:
            print "Copy Error: This copy already exists"
            return 0
        config = os.path.join(new,"config")
        coms = [a for a in os.listdir(config) if '.' not in a]
        for com in coms:
            driver.write_driver(com, new)
