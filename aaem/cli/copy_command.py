"""
run_command.py

    A commad for the cli to copy a model run
"""
import pycommand
import shutil
import os.path 

class CopyCommand(pycommand.CommandBase):
    """
    copy command class
    """
    usagestr = 'usage: copy [options] source destination'
    description = 'set up a new model run based off an old one'
    
    optionList = (
            ('force',('f', False, "force overwrite of existing directorys")),
                
                 )
    description = ('Set up a new model run based off an old one\n\n'
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
        if self.args and os.path.exists(self.args[0]):
            source = os.path.abspath(self.args[0])
        else:
            msg =  "COPY ERROR: source must exist"
            cli_lib.print_error_message(msg, CopyCommand.usagestr)
            return 0
    
        if self.args:
            try:
                dest = os.path.abspath(self.args[1])
            except IndexError:
                msg = "COPY ERROR: destination needed"
                cli_lib.print_error_message(msg, CopyCommand.usagestr)
                return 0
                
        force = True
        if self.flags.force is None:
            force = False
        
        if os.path.exists(dest) and not force:
            msg = "COPY ERROR: " + dest + \
                            " exists. Use force flag (-f) to overwrite"
            cli_lib.print_error_message(msg, CopyCommand.usagestr)
            return
        
        try:
            shutil.rmtree(dest)
        except OSError:
            pass
            
        print "Copying ..."
        
        for sd in ['config', 'input_files']:
            shutil.copytree(os.path.join(source, sd), os.path.join(dest, sd))
