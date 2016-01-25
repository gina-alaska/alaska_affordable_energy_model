"""
help_command.py

    A commad for the cli to provide help on the cli's commands
"""
import pycommand
import aaem.cli

class HelpCommand(pycommand.CommandBase):
    """
    help command class
    """
    usagestr = 'usage: help [command]'
    description = ('Prints info on provided command')
    
    def run(self):
        """
        run the command
        """
        if self.args and self.args[0] in aaem.cli.AaemCommand.commands.keys():
            print aaem.cli.AaemCommand.commands[self.args[0]].usagestr
            print aaem.cli.AaemCommand.commands[self.args[0]].description
            return 0
        elif self.args:
            print ("command: [" + self.args[0] + "] not recongnized.\n"
            "  avaliable commands: " + str(aaem.cli.AaemCommand.commands.keys()) 
                    )
        else:
            print aaem.cli.AaemCommand.usagestr
            print aaem.cli.AaemCommand.description    
    
