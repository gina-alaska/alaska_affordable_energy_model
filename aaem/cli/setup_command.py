import pycommand
import sys

class SetupCommand(pycommand.CommandBase):
    usagestr = 'usage: setup [directory]'
    description = 'Set up directory for running AAEM Models'

    def run(self):
        print('Python version ' + sys.version.split()[0])