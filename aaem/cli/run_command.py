"""
run_command.py

    A commad for the cli to run the model
"""
import pycommand
from default_cases import __DEV_COMS_RUN__ as __DEV_COMS__ 
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
            ('plot',('p', '<directory>', 
                        "run the ploting functionality and save in directory")),
            ('force',('f', False, "force overwrite of existing directories")),
            ('config',('c','<directory>', "alternate config directory")),
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
        # get arguments
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            print
            print "RUN ERROR: needs a directory"
            print RunCommand.usagestr
            print
            return 0
        
        # Get communites to run
        if self.flags.dev:
            # Developmet coms
            coms = __DEV_COMS__
        elif len(self.args[1:]) != 0:
            # listed coms
            coms = self.args[1:]
            if len(coms) == 1:
                # Regional coms
                region = coms[0]
                coms = cli_lib.get_regional_coms(region, base)
        else:
            # ALL COMS
            coms = cli_lib.get_config_coms(base)
        
        # other options
        plot = False
        img_dir = None
        if not self.flags.plot is None:
            plot = True    
            img_dir = self.flags.plot
        
        force = True
        if self.flags.force is None:
            force = False
            
        alt_config = None
        if not self.flags.config is None:
            alt_config = self.flags.config
        
        if os.path.exists(os.path.join(base,'results')) and force:
            shutil.rmtree(os.path.join(base,'results'))
        elif os.path.exists(os.path.join(base,'results')):
            print
            print "RUN ERROR: " + os.path.join(base,'results') + \
                        " exists. Use force flag (-f) to overwrite"
            print
            return 0
    
        
        # add these options
        #~ name = None 
        #~ i_dir = None
        #~ c_config = None 
        #~ g_config = None
        #~ tag = '' 
    
        sout = sys.stdout
        if self.flags.log:
            sys.stdout  = open(self.flags.log, 'w')
            
        run_driver = driver.Driver(base)
        for com in sorted(coms):
            print com
            #~ try:
            run_driver.run(com, 
                    c_config = cli_lib.get_alt_community_config(alt_config,com),
                    img_dir = img_dir,
                    plot = plot)
            #~ except RuntimeError as e :
                #~ print e
                #~ print
                #~ print "RUN ERROR: "+ com + " not a configured community/project"
                #~ print
                
        try:
            run_driver.save_summaries()
        except IOError:
            print
            print "RUN ERROR: No valid communities/projects provided"
            print
            return 0
        run_driver.save_metadata()
        
        sys.stdout = sout
        
