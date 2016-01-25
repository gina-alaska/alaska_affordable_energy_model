"""
run_command.py

    A commad for the cli to list communities
"""
import pycommand
import os.path


class ListCommand(pycommand.CommandBase):
    """
    list command class
    """
    usagestr = 'usage: list  path_to_model'

    description = ('List Communities that can be run.\n')

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            print  "List Error: needs a existing run"
            return 0
        

        config = os.path.join(base,"config")
        coms = [a for a in os.listdir(config) if '.' not in a]
        for com in coms:
            print com
