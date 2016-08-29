"""
run_command.py

    A commad for the cli to compare runs
"""
import pycommand
import os.path
import filecmp

import cli_lib



class CompareCommand(pycommand.CommandBase):
    """
    compare command class
    """
    usagestr = ('usage: compare path_to_results_1 path_to_results_2'
                    ' [list_of_communities (with underscores)]')

    description = ('compares results of two model runs. If a list of'
                   ' communities is provided, an in depth by provided\n')

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]) \
                     and os.path.exists(self.args[1]):
            results1 = os.path.abspath(self.args[0])
            results2 = os.path.abspath(self.args[1])
        else:
            msg = "Compare Error: needs 2 existing runs"
            cli_lib.print_error_message(msg, CompareCommand.usagestr)
            return 0
        
        
        coms = self.args[2:]
        if len(coms) != 0 :
            cli_lib.compare_indepth(results1, results2, coms)
        else:
            cli_lib.compare_high_level(results1, results2)

        

