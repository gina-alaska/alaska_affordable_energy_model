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

from aaem import driver


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
            ('tag',('t', '<tag>', "tag for results directory")),
            ('scalers', ('s', '<scalers>',
                                    'dictioanry of scalers as a string')),
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
    
        # log file?
        sout = sys.stdout
        if self.flags.log:
            sys.stdout  = open(self.flags.log, 'w')
    
        if self.args and os.path.exists(self.args[0]):
            base = os.path.abspath(self.args[0])
        else:
            msg = "RUN ERROR: needs a directory"
            cli_lib.print_error_message(msg, RunCommand.usagestr)
            return 0
            
        force = True
        if self.flags.force is None:
            force = False
        
        if os.path.isfile(base):
        #run script
            print 'Runnint script ...'
            
            try:
                script  = driver.script_validator(base)
            except StandardError as e:
                cli_lib.print_error_message('SCRIPT ERROR:\n' + str(e))
                return 0
            
            ## check exitsing results
            res_dir = 'results'
            if script['global']['results tag']:
                res_dir += '_' + script['global']['results tag']
            base = script['global']['root']
            
            #~ print os.path.join(base, res_dir)
            if os.path.exists(os.path.join(base, res_dir)) and force:
                shutil.rmtree(os.path.join(base, res_dir))
            elif os.path.exists(os.path.join(base, res_dir)):
                msg =  "RUN ERROR: " + os.path.join(base, res_dir) + \
                            " exists. Use force flag (-f) to overwrite"
                cli_lib.print_error_message(msg, RunCommand.usagestr)
                return 0
            
            # run
            run_driver = driver.Driver(base)
            
            for com in script['communities']:
                print 'community:', com['community'], 'name:', com['name']
                try:
                    mult = script['global']['construction multipliers']
                    run_driver.run(com['community'], com['name'],
                                   i_dir = com['input files'],
                                   c_config = com['config'],
                                   g_config = script['global']['config'],
                                   img_dir = script['global']['image diretory'],
                                   plot = script['global']['plot'],
                                   tag = script['global']['results tag'],
                                   c_mult = mult,
                                   scalers = com['scalers'])
                except (RuntimeError, IOError) as e:
                    print e
                    msg = "RUN ERROR: "+ com['community'] + \
                                " not a configured community/project"
                    cli_lib.print_error_message(msg)
                
            # save Summaries
            try:
                run_driver.save_summaries(script['global']['results tag'])
            except IOError as e :
                #~ print e
                msg = "RUN ERROR: No valid communities/projects provided"
                cli_lib.print_error_message(msg)
                return 0
            run_driver.save_metadata(script['global']['results tag'])
                    
        else:
            # run regular
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
                try:
                    coms = cli_lib.get_config_coms(base)
                except OSError:
                    msg = ("RUN ERROR: structure to run model does "
                                            "not exist at provided path")
                    cli_lib.print_error_message(msg)
                    return 0
            # other options
            plot = False
            img_dir = None
            if not self.flags.plot is None:
                plot = True    
                img_dir = self.flags.plot
            
            tag = ''
            if not self.flags.tag is None:
                tag = self.flags.tag
            if tag != '':
                rd = 'results_' + tag 
            else:
                rd = 'results'
                
            scalers = driver.default_scalers
            if not self.flags.scalers is None:
                items = self.flags.scalers.replace('{','').\
                                           replace('}','').\
                                           strip().split(',')
                for i in items:
                    item = i.split(":")
                    key = item[0].strip().strip('"\'')
                    try:
                        #~ print scalers
                        scalers[key]
                    except KeyError:
                        msg = "SCALER ERROR: " + key + " is not a valid scaler"
                        cli_lib.print_error_message(msg)
                        return 0
                    scalers[key] = float(item[1])                                    
                
            ## results exist?
            if os.path.exists(os.path.join(base, rd)) and force:
                shutil.rmtree(os.path.join(base, rd))
            elif os.path.exists(os.path.join(base, rd)):
                msg =  "RUN ERROR: " + os.path.join(base, rd) + \
                            " exists. Use force flag (-f) to overwrite"
                cli_lib.print_error_message(msg, RunCommand.usagestr)
                return 0
            
            ## Run 
            run_driver = driver.Driver(base)
            for com in sorted(coms):
                print com
                try:
                    run_driver.run(com, img_dir = img_dir,
                                    plot = plot, tag = tag, scalers = scalers)
                except (RuntimeError, IOError) as e:
                    msg = "RUN ERROR: "+ com + \
                                    " not a configured community/project"
                    cli_lib.print_error_message(msg)
            
            # save summaries
            try:
                run_driver.save_summaries(tag)
            except IOError:
                msg = "RUN ERROR: No valid communities/projects provided"
                cli_lib.print_error_message(msg)
                return 0
            run_driver.save_metadata(tag)
            
        sys.stdout = sout
        
