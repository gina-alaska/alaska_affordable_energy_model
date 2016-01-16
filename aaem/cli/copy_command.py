import pycommand
import shutil
import os.path
from aaem import driver
from datetime import datetime

class CopyCommand(pycommand.CommandBase):
    usagestr = 'usage: copy -t <tag> [old path]'
    description = 'set up a new model run based off an old one'
    
    optionList = (
           ('tag', ('t', "<name>", "tag for run directory")),
    )

    def run(self):
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            print  "copy needs a directory"
            return 0
    
        
        model_root = os.path.split(base)[0]
        
        if self.flags.tag:
            tag = self.flags.tag
        else:
            tag = datetime.strftime(datetime.now(),"%Y%m%d%H%M%S")
        new = os.path.join(model_root,"run_" + tag)
        
        try:
            shutil.copytree(os.path.join(base,"input_data"), os.path.join(new,"input_data"))
            shutil.copytree(os.path.join(base,"config"), os.path.join(new,"config"))
        except OSError:
            pass
        config = os.path.join(new,"config")
        print config
        coms = [a for a in os.listdir(config) if '.' not in a]
        print coms
        for com in coms:
            print com
            driver.write_driver(com, new)
