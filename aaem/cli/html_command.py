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

from aaem_summaries import web


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
                   replace(']','').replace(',','\n') 
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
        
        #~ try:
        ws.generate_all()
        try:
            pth = os.path.join(out, 'Barrow')
            os.rename(pth, pth.replace('Barrow','Utqiagvik'))
            
            pth = os.path.join(out, 'Utqiagvik', 'csv')
            for f_name in os.listdir(pth):
                f = os.path.join(pth, f_name)
                #~ print f
                os.rename(f,f.replace('Barrow','Utqiagvik'))
            
            pth = os.path.join(out, 'Utqiagvik')
            for f_name in os.listdir(pth):
                if f_name.find('.html') != -1:
                    f = os.path.join(pth,f_name)
                    with open(f,'r') as in_f:
                        text = in_f.read()
                    with open(f,'w') as out_f:
                        out_f.write(text.replace('Barrow','Utqiagvik'))
            
            
            f = os.path.join(out,'map.js')
            with open(f,'r') as in_f:
                text = in_f.read()
            with open(f,'w') as out_f:
                out_f.write(text.replace('Barrow','Utqiagvik'))
            f = os.path.join(out,'navbar.js')
            with open(f,'r') as in_f:
                text = in_f.read()
            with open(f,'w') as out_f:
                out_f.write(text.replace('Barrow','Utqiagvik'))
        except:
            pass
        
        print 'Complete'
        
        
