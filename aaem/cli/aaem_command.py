import pycommand
import sys

from aaem.cli.run_command import RunCommand
from aaem.cli.setup_command import SetupCommand
from aaem.cli.copy_command import CopyCommand

class AaemCommand(pycommand.CommandBase):
    usagestr = 'usage: aaem <command>'
    description = (
        'Commands:\n'
        '  setup        Set up workspace for running aaem models\n'
        '  run          Run aaem model\n'
        '  copy         Create a copy of a model run\n'
    )

    commands = {
        'setup': SetupCommand,
        'run':   RunCommand,
        'copy':  CopyCommand,
        }

    def run(self):
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
            return cmd.run()
