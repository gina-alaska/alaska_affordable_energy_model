"""
run_command.py

    A command for the cli to run the model
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
            #~ ('plot',('p', '<directory>', 
                        #~ "run the plotting functionality and save in directory")),
            ('force',('f', False, "force overwrite of existing directories")),
            ('tag',('t', '<tag>', "tag for results directory")),
            ('scalers', ('s', '<scalers>',
                                    'dictionary of scalers as a string')),
            ('global_config', ('g', '<global_configuration_file>', 
                ('A configuration yaml file containing variables to apply'
                ' all communities being run'))),
           )
    description =('Run model for given communities. (default = all communities)'
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
            #~ print 'Runnint script ... need to reimplement'
            
            try:
                script = driver.script_validator(base)
            except StandardError as e:
                cli_lib.print_error_message('SCRIPT ERROR:\n' + str(e))
                return 0
            
            ## check existing results
            res_dir = 'results'
            if script['global']['results tag']:
                res_dir += '_' + script['global']['results tag']
            base = script['global']['root']
            
            #~ ## print os.path.join(base, res_dir)
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
                print 'community:', com['community'], 'name:', com['ID']
                try:
                    #~ print com['config']
                    run_driver.run(
                        com['config'],
                        global_config = script['global']['global config'],
                        tag = script['global']['results tag'],
                        scalers = com['scalers'],
                        alt_save_name = com['ID'])
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
            # Get communities to run
            if self.flags.dev:
                # Development coms
                coms = __DEV_COMS__
            elif len(self.args[1:]) != 0:
                # listed coms
                coms = self.args[1:]
                if len(coms) == 1:
                    if coms[0][-1] == '*':
                        coms = [c for c in cli_lib.get_config_coms(base) \
                            if c.find(coms[0][:-1]) != -1]
                        #~ print coms
                    else:
                        # Regional coms
                        region = coms[0]
                        coms = cli_lib.get_regional_coms(region, base)
                # model thinks its barrow
                if 'Utqiagvik' in coms:
                    coms[coms.index('Utqiagvik')] = 'Barrow'
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
            #~ plot = False
            #~ img_dir = None
            #~ if not self.flags.plot is None:
                #~ plot = True    
                #~ img_dir = self.flags.plot
            
            tag = ''
            if not self.flags.tag is None:
                tag = self.flags.tag
            if tag != '':
                rd = 'results_' + tag 
            else:
                rd = 'results'
               
            global_config = None
            if not self.flags.global_config is None:
                global_config = self.flags.global_config
                if not os.path.isfile(global_config):
                    msg = 'FLAG ERROR: global config specified with option' + \
                        ' --global(-g) is not a file'
                    raise RuntimeError, msg
            if global_config is None:
                gc = os.path.join(base, 'config', '__global_config.yaml')
                if os.path.isfile(gc):
                    print 'Using ' + gc + ' ad global config'
                    global_config = gc 
        
        
                
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
            #~ print sorted(coms)
            run_driver = driver.Driver(base)
            for com in sorted(coms):
                if com == 'Barrow':
                    print 'Utqiagvik'
                else:
                    print com
                try:
                    pth = os.path.join(base,'config',com + '.yaml')
                    run_driver.run(
                        pth, 
                        global_config = global_config,
                        tag = tag, 
                        scalers = scalers
                    )
                                    
                except (RuntimeError, IOError) as e:
                    print e
                    msg = "RUN ERROR: "+ com + \
                                    " not a configured community/project"
                    cli_lib.print_error_message(msg)
            
            # save summaries
            try:
                run_driver.save_summaries(tag)
            except IOError as e:
                print e
                msg = "RUN ERROR: No valid communities/projects provided"
                cli_lib.print_error_message(msg)
                return 0
                
            try:
                name =  'Utqiagvik'
                os.rename(os.path.join(base, rd, 'Barrow'),
                            os.path.join(base, rd, 'Utqiagvik_Barrow'))
                for f_name in os.listdir(os.path.join(base, rd, 
                                                        'Utqiagvik_Barrow')):
                    if f_name.find('.csv') != -1:
                        f = os.path.join(base, rd, 'Utqiagvik_Barrow',f_name)
                        with open(f,'r') as in_f:
                            text = in_f.read()
                        with open(f,'w') as out_f:
                            out_f.write(text.replace('Barrow',
                                                            'Utqiagvik (Barrow)'))
                        #~ print f
                        os.rename(f,
                            os.path.join(base, rd, 'Utqiagvik_Barrow',
                                f_name.replace('Barrow','Utqiagvik_Barrow')))
                for f_name in os.listdir(os.path.join(base, rd, 'Utqiagvik_Barrow','component_outputs')):
                    #~ print f_name
                    if f_name.find('.csv') != -1:
                        f = os.path.join(base, rd, 'Utqiagvik_Barrow','component_outputs',f_name)
                        with open(f,'r') as in_f:
                            text = in_f.read()
                        with open(f,'w') as out_f:
                            out_f.write(text.replace('Barrow','Utqiagvik (Barrow)'))
                        #~ print f
                        os.rename(f,
                            os.path.join(base, rd, 'Utqiagvik_Barrow','component_outputs',
                                f_name.replace('Barrow','Utqiagvik_Barrow')))
            except StandardError as e:
                # no need to do any thing if 'Barrow','Utqiagvik' not necessary
                #~ print e
                pass
            run_driver.save_metadata(tag)
            
        sys.stdout = sout
        
