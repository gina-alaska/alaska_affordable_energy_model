import pycommand
import sys
import os.path

class SetupCommand(pycommand.CommandBase):
    usagestr = 'usage: setup [directory]'
    description = 'Set up directory for running AAEM Models'

    optionList = (
        ('name', ('-n', "<name>", "name of model")),
        
    )

    def run(self):
        
        print('Python version ' + sys.version.split()[0])
        print('Path: ' + os.getcwd())
        path = os.getcwd()
        
        
        
        
        print self.flags
        
        if self.flags.name:
            print self.flags.name
            name = '_' + self.flags.name
        else:
            name = ""
        
        
        
        try:
            os.makedirs(os.path.join(path,"model" + name))
        except OSError:
            pass

if __name__ == '__main__':
    # Shortcut for reading from sys.argv[1:] and sys.exit(status)
    pycommand.run_and_exit(SetupCommand)
