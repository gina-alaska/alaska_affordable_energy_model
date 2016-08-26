"""
run_command.py

    A commad for the cli to run the model
"""
import pycommand
from aaem import __version__, __download_url__ , summaries
from default_cases import __DEV_COMS_RUN__ as __DEV_COMS__ 
from datetime import datetime
from pandas import read_csv
import os.path
import shutil
import sys
import cli_lib

from aaem import driver_2 as driver




class RunCommand(pycommand.CommandBase):
    """
    run command class
    """
    usagestr = ('usage: run path_to_model_run '
                                    '[list_of_communities (with underscores)] ')
    optionList = (
            ('dev', ('d', False, "use only development communities")),
            ('log', ('l', "<log_file>", "name/path of file to log outputs to")),
            ('plot',('p', False, "run the ploting functionality")),
           )
    description =('Run model for given communities. (default = all communities)'
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
        start = datetime.now()
        
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
            img_dir = os.path.join(base,'results','__images')
        else:
            print  "run needs a directory"
            return 0
        
        config = os.path.join(base,"config")
        
        gc = '__global_config.yaml'
        
        if len(self.args[1:]) != 0:
            coms = self.args[1:]
        else:
            s_text = '_config.yaml'
            coms = [a.split(s_text)[0]\
                        for a in os.listdir(config) if (s_text in a and gc != a)]
    
        if self.flags.dev:
            coms = __DEV_COMS__
     
        if len(coms) == 1:
            region = coms[0]
            coms = cli_lib.get_regional_coms(region, base)
            #~ if coms = []:
                #~ print "Region " + region + " is not a valid energy region"
                #~ return
        
        plot = False
        if self.flags.plot:
            plot = True    
        
        try:
            shutil.rmtree(os.path.join(base,'results'))
        except OSError:
            pass
        
        # add these options
        #~ name = None 
        #~ i_dir = None
        #~ c_config = None 
        #~ g_config = None
        #~ tag = '' 
        #~ img_dir = None 
        
        sout = sys.stdout
        if self.flags.log:
            sys.stdout  = open(self.flags.log, 'w')
            
        run_driver = driver.Driver(base)
        coms = sorted(coms)
    
        for com in coms:
            print com
            run_driver.run(com)
        run_driver.save_summaries()
        run_driver.save_metadata()
        
        sys.stdout = sout
        
