"""
cli_lib.py

    functionality used by multiple cli commands
"""
import os
import shutil
from pandas import read_csv, concat
from aaem import summaries, __version__
from aaem.components import get_raw_data_files
import zipfile
from datetime import datetime
   
def list_files (directory, root = None):
    """ Function doc """
    l = []
    if root is None:
        root = directory
    for item in os.listdir(directory):
        if item[0] == '.':
            continue
        if not os.path.isdir(os.path.join(directory,item)):
            l.append(os.path.join(directory.replace(root,""),item))
        else:
            l += list_files(os.path.join(directory,item),root)
    return l
    
def compare_indepth (results1, results2, coms):
    """
    """
    print "#####################################"
    for c in coms:
        print "Community: " + c
        print ""
        com1 = os.path.join(results1,c)
        com2 = os.path.join(results2,c)
        
        files1 = list_files(com1)
        files2 = list_files(com2)
        
        
        files1 = set(files1) 
        files2 = set(files2)
        print "Results 1: " + com1
        print ""
        print "Results 2: " + com2
        print ""
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
            print "Same files found in results 1 and 2"
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
                        diff.append(f)
                    else:
                        same.append(f)
                except StandardError as e:
                    error.append(f)
                    reason.append(e)
                except:
                    error.append(f)
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
    
def compare_high_level (results1, results2):
    """ Function doc """
    
    files1 = set([f for f in list_files(results2) \
                if os.path.isfile(os.path.join(results1,f))])
    files2 = set([f for f in list_files(results2) \
                if os.path.isfile(os.path.join(results2,f))])
    
    print "compating all communities (log files)"
    
    print "Results 1: " + results1
    print ""
    print "Results 2: " + results2
    print ""
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
        print "Same files found in results 1 and 2"
        
    to_compare = files1 & files2
    print "Test 2: Comparing Logs"
    print ""
    
    for f in to_compare:
        if ".pkl" in f:
            continue
        f1 = read_csv(os.path.join(results1,f), index_col = 0, comment = '#').fillna("null")
        f2 = read_csv(os.path.join(results2,f), index_col = 0, comment = '#').fillna("null")
        print "summary: " + f
        print ""
        if (set(f1.index) ^ set(f2.index)) != 0:
            d1 = set(f1.index) - set(f2.index)
            d2 = set(f2.index) - set(f1.index)
            print "\tthe following communities found in results 1 but not 2"
            for c in d1:
                print "\t\t" + c 
            print ""
            print "\tthe following files communities in results 2 but not 1"
            for c in d2:    
                print "\t\t" + c
            print ""
            
        to_compare = set(f1.index) & set(f2.index)
        print "\tfinding differences in available communites:"
        for c in sorted (to_compare):
            try:
                if (f1.ix[c] != f2.ix[c]).any():
                    print "\t\tdifferences found in " + c
                #~ print ""
                #~ k = f1.keys()[f1.ix[c] != f2.ix[c]] 
                #~ if len(k) !=  len(f1.keys()):
                     
                    #~ print concat([f1.ix[c],f2.ix[c]],axis=1).T[k]
                #~ else:
                    #~ print "all differents"
            except ValueError:
                print "\t\tdifferences found in " + c
             
def get_regional_coms (region, base):
    """
    get a list of communities and projects for a region
    
    input:
        region: a region <str>
        com_list: Pathe to the model version directory being run
        
    output:
        return a sorted list of projects and communities <list>
    
    """
    com_file = os.path.join(base, 'config', '__community_list.csv')
    com_file = read_csv(com_file, index_col = 0)
    
    if not (region in set(com_file['Energy Region'].values)):
        return [region]
    
    lis = [x.replace(' ','_') for x in \
                com_file[com_file['Energy Region'] == region]\
                ['Community'].values.tolist()] 
    coms = []
    
    
    config = os.path.join(base, 'config')
    gc = '__global_config.yaml'
    s_text = '_config.yaml'
    all_coms = [a.split(s_text)[0]\
                        for a in os.listdir(config) if (s_text in a and gc != a)]
    
    for c in lis:
        coms += [x for x in all_coms if x.find(c) != -1]
    return sorted(coms)
                
def get_config_coms (base):
    """
    get the communities/projects that have configuration information available
    
    input:
        base: path to model
        
    output:
        returns list of communities/projects
    """
    config = os.path.join(base,"config")
    gc = '__global_config.yaml'
    s_text = '_config.yaml'
    return [a.split(s_text)[0]\
                    for a in os.listdir(config) if (s_text in a and gc != a)]
    
def print_error_message (msg, use = None):
    """
    print an errom message to the console
    
    input:
        msg: the message <string>
        use: (optional) the useage string for the command <string>
        
    output:
        none
    """
    print 
    print msg
    if not use is None:
        print use
    print 
