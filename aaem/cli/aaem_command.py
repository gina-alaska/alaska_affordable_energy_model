import warnings
import pycommand
import sys

from aaem.cli.run_command import RunCommand
from aaem.cli.setup_command import SetupCommand
from aaem.cli.copy_command import CopyCommand
from aaem.cli.help_command import HelpCommand
from aaem.cli.list_command import ListCommand
from aaem.cli.compare_command import CompareCommand
from aaem.cli.refresh_command import RefreshCommand
from aaem.cli.html_command import HtmlCommand
from aaem.cli.get_data_command import GetDataCommand

from datetime import datetime



class AaemCommand(pycommand.CommandBase):
    usagestr = 'usage: aaem <command>'
    description = (
        'Commands:\n'
        '  setup        Set up workspace for running aaem models\n'
        '  run          Run aaem model\n'
        '  copy         Create a copy of a model run\n'
        '  help         See info on a given commands\n'
        '  list         List communities in a model run\n'
        '  compare      compare the results of 2 model runs\n'
        '  refresh      refresh the data in the model\n'
        '  summaries         create web summaries\n'
        '  get-data     create data needed for the model\n'
    )

    commands = {
        'setup': SetupCommand,
        'run':   RunCommand,
        'copy':  CopyCommand,
        'help': HelpCommand,
        'list': ListCommand,
        'compare': CompareCommand,
        'refresh': RefreshCommand,
        'summaries': HtmlCommand,
        'get-data': GetDataCommand,
        }
        
    optionList = (
            ('warn', ('w', False, "show all warnings")),
            ('time',('t', False,
                    "Displays the total running time at the end of execution")),
           #~ ('path', ('p', "<name>", "path to location to setup/run  model")),
           #~ ('name', ('n', "<name>", "name of model")),
    )

    def run(self):
        # ignore warings in cli
        if not self.flags.warn:
            warnings.filterwarnings("ignore")
            
        try:
            cmd = super(AaemCommand, self).run()
        except pycommand.CommandExit as e:
            return e.err
        
        
        #~ cmd.registerParentFlag('name', SetupCommand.flags.name)
        
        if cmd.error:
            print('aaem {cmd}: {error}'
                  .format(cmd=self.args[0], error=cmd.error))
            return 1
        else:
            start = datetime.now()
            res = cmd.run()
            if self.flags.time:
                print "total run time: " + str(datetime.now() - start)
            return res
