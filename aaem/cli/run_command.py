import pycommand
from aaem import driver
import os.path

class RunCommand(pycommand.CommandBase):
    usagestr = 'usage: run [path to run dir] '
    description = 'Run model for given communities. (default = all communities)'

    def run(self):
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            print  "run needs a directory"
            return 0
        config = os.path.join(base,"config")
        coms = [a for a in os.listdir(config) if '.' not in a]
        batch = {}
        for com in coms:
            batch[com] = os.path.join(config,com,com+"_driver.yaml")
        driver.run(batch, "")
