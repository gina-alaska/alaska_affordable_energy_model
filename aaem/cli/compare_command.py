"""
run_command.py

    A commad for the cli to compare runs
"""
import pycommand
import os.path
import filecmp


class CompareCommand(pycommand.CommandBase):
    """
    compare command class
    """
    usagestr = 'usage: compare path_to_model_1 path_to_model_2'

    description = ('compare two runs results.\n')

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]) \
                     and os.path.exists(self.args[1]):
            path1 = os.path.join(os.path.abspath(self.args[0]),'results')
            path2 = os.path.join(os.path.abspath(self.args[1]),'results')
        else:
            print  "Compare Error: needs 2 existing runs"
            return 0
        
        comp = filecmp.dircmp(path1,path2)

        print comp.report_full_closure()
