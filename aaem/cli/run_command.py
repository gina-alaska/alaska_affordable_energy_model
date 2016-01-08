import pycommand

class RunCommand(pycommand.CommandBase):
    usagestr = 'usage: run [community ...]'
    description = 'Run model for given communities. (default = all communities)'

    def run(self):
        print('Running Stuff')