"""
run_command.py

    A commad for the cli to compare runs
"""
import pycommand
import os.path
import filecmp

from pandas import read_csv
import cli_lib



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
            results1 = os.path.join(os.path.abspath(self.args[0]),'results')
            results2 = os.path.join(os.path.abspath(self.args[1]),'results')
        else:
            print  "Compare Error: needs 2 existing runs"
            return 0
        
        try:
            coms = self.args[2:]
        except IndexError:
            print  "Compare Error: please provide a community "
            return 0
        
        
        for c in coms:
            print "Community: " + c
            com1 = os.path.join(results1,c)
            com2 = os.path.join(results2,c)
            
            files1 = cli_lib.list_files(com1)
            files2 = cli_lib.list_files(com2)
            
            
            files1 = set(files1) 
            files2 = set(files2)
            
            # a ^ b set semmetric difference a not in b union b not in a
            # a - b set diffrence. a not in b 
            print "Test 1: testing for different files"
            print ""
            if len(files1 ^ files2) != 0:
                d1 = files1 - files2
                d2 = files2 - files1
                print "the following files found in results 1 but not 2"
                print ""
                for f in d1:
                    print "\t" + f 
                print ""
                print "the following files found in results 2 but not 1"
                print ""
                for f in d2:
                    print "\t" + f 
                
            else:
                print "Same files found in results 2 and 1"
            print ""
            print "---------------------------------"
            print "Test 2: checking each files data (skips diagnostic files)"
            print ""
            
            
            to_compare = files1 & files2
        
            same = []
            diff = []
            error = []
            reason = []
            for f in to_compare:
                if f.find("diagnostics") != -1 :
                    continue
                #~ print com1, com2
                f1 = os.path.join(com1,f)
                f2 = os.path.join(com2,f)
                f1 = com1 +'/' + f
                f2 = com2 +'/' + f
                if f.find('.csv') != -1:
                    try:
                        try:
                            data1 = read_csv(f1,index_col=0,
                                        comment="#").fillna(-9999)
                            data2 = read_csv(f2,index_col=0,
                                    comment="#").fillna(-9999)
                        except:
                            data1 = read_csv(f1,index_col=0,
                                    comment="#",skiprows=4).fillna(-9999)
                            data2 = read_csv(f2,index_col=0,
                                    comment="#",skiprows=4).fillna(-9999)
                        #~ print data1
                        #~ print data2
                    
                        if ((data1 == data2).values == False).any():
                            #~ print data1 == data2
                            #~ print "File: " + f + " has differences between versions"
                            diff.append(f)
                        else:
                            #~ print "File: " + f + " is the same between versions"
                            same.append(f)
                    except StandardError as e:
                        error.append(f)
                        reason.append(e)
                    except:
                        error.append(f)
                        #~ print "File: " + f + " could not caompare between versions"
            print "The following files were the different between versions:"
            for f in diff:
                print "\t" +f 
            print ""
        
            print "The following files could not be compared between versions:"
            for f in error:
                print "\t" +f 
                print "\t\t" + str(e)
            print ""
            
            print "The following files were the same between versions:"
            for f in same:
                print "\t" +f 
            print ""
            print "#####################################"
            print ""
        
        #~ comp = filecmp.dircmp(path1,path2)

        #~ print comp.report_full_closure()
