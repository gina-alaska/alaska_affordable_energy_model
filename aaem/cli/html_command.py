"""
run_command.py

    A command for the cli to generate summaries
"""
import pycommand
from default_cases import __DEV_COMS_RUN__ as __DEV_COMS__ 
import os
import shutil
import sys
import cli_lib

from aaem import web


class HtmlCommand(pycommand.CommandBase):
    """
    run command class
    """
    usagestr = ('usage: run <options> path_to_model <tag> ')
    optionList = (
            ('alt_out', ('a', '<path>', "alterante output location")),
            ('force',('f', False, "force overwrite of existing directories")),
           )
    description =('genearate html summaries'
                    'options: \n'
                   "  " + str([o[0] + ': ' + o[1][2] + '. Use: --' +\
                   o[0] + ' (-'+o[1][0]+') ' +  (o[1][1] if o[1][1] else "")  +\
                   '' for o in optionList]).replace('[','').\
                   replace(']','').replace(',','\n ') 
                )
                
    def run(self):
        """
        run the command
        """
        # get arguments
    
        # log file?
        if self.args and os.path.exists(self.args[0]):
            root = os.path.abspath(self.args[0])
        else:
            msg = "HTML ERROR: needs path to model folder"
            cli_lib.print_error_message(msg, self.usagestr)
            return 0
            
        try:
            tag = self.args[1]
        except IndexError:
            tag = ''
            
            
        if self.flags.alt_out is None:
            ot = tag
            if ot != '':
                ot = '_' + ot
            out = os.path.join(root, 'results' + ot, '__web_summaries')
        else:
            out = self.flags.alt_out
        
        force = True
        if self.flags.force is None:
            force = False
            
        if os.path.exists(out) and force:
                shutil.rmtree(out)
        elif os.path.exists(out):
            msg =  "HTML ERROR: " + out + \
                        " exists. Use force flag (-f) to overwrite"
            cli_lib.print_error_message(msg, self.usagestr)
            return 0
        
        print "Loading Results..."
        ws = web.WebSummary(root, out, tag)
        print "Generating Summaries..."
        ws.generate_all()
        print 'Complete'
        
