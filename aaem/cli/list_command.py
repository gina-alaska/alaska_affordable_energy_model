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
    usagestr = 'usage: list path_to_model'

    description = ('List Communities that can be run from standard '
                        'setup directory.\n')

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            msg = "LIST ERROR: needs a existing run"
            cli_lib.print_error_message(msg, ListCommand.usagestr)
            return 0
        

        config = os.path.join(base,"config")
        gc = '__global_config.yaml'
        s_text = '_config.yaml'
        coms = [a.split(s_text)[0]\
                        for a in os.listdir(config) if (s_text in a and gc != a)]
        for com in coms:
            print com
