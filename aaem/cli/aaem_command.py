import pycommand
import sys

from aaem.cli.run_command import RunCommand
from aaem.cli.setup_command import SetupCommand

class AaemCommand(pycommand.CommandBase):
    usagestr = 'usage: aaem <command>'
    description = (
        'Commands:\n'
        '  setup        Set up workspace for running aaem models\n'
        '  run          Run aaem model'
    )

    commands = {
        'setup': SetupCommand,
        'run':   RunCommand        }

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
