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
    usagestr = ('usage: compare path_to_model_1 path_to_model_2'
                    ' [list_of_communities (with underscores)]')

    description = ('compares results of two model runs. If a list of'
                   ' communities is provided, an in depth by provided\n')
                  #~ # ' community comparsion will take place. Otherwise a high'
                  #~ #' level comparsion of all communites will occur\n')

    def run(self):
        """
        run the command
        """
        if self.args and os.path.exists(self.args[0]) \
                     and os.path.exists(self.args[1]):
            results1 = os.path.join(os.path.abspath(self.args[0]),'results')
            results2 = os.path.join(os.path.abspath(self.args[1]),'results')
        else:
            print  "Compare Error: needs 2 existing runs"
            return 0
        
        
        coms = self.args[2:]
        if len(coms) != 0 :
            cli_lib.compare_indepth(results1, results2, coms)
        else:
            cli_lib.compare_high_level(results1, results2)

        

        
        #~ comp = filecmp.dircmp(path1,path2)

        #~ print comp.report_full_closure()
