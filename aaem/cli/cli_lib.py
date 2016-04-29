"""
cli_lib.py

    functionality used by multiple cli commands
"""
import os
import shutil
from pandas import read_csv, concat
from aaem import summaries



def copy_model_data (repo, raw):
    """
        copies the data needed to run the model from the data repo to the raw 
    data folder.
    
    pre:
        repo : path to the data repo
        raw: path to the raw data folder
    post:
        the files used to run the preprocessor are copied to the raw directory
    """
    shutil.copy(os.path.join(repo,
                    "power-cost-equalization-pce-data.csv"), raw)
    shutil.copy(os.path.join(repo, "com_building_estimates.csv"), raw)
    shutil.copy(os.path.join(repo, "com_num_buildings.csv"), raw)
    shutil.copy(os.path.join(repo, "cpi.csv"), raw)
    shutil.copy(os.path.join(repo, "diesel_fuel_prices.csv"), raw)
    shutil.copy(os.path.join(repo, "eia_generation.csv"), raw)
    shutil.copy(os.path.join(repo, "eia_sales.csv"), raw)
    shutil.copy(os.path.join(repo, "hdd.csv"), raw)
    shutil.copy(os.path.join(repo, "heating_fuel_premium.csv"), raw)
    shutil.copy(os.path.join(repo, "interties.csv"), raw)
    shutil.copy(os.path.join(repo, "non_res_buildings.csv"), raw)
    shutil.copy(os.path.join(repo, "population.csv"), raw)
    shutil.copy(os.path.join(repo, "population_neil.csv"), raw)
    shutil.copy(os.path.join(repo, "purchased_power_lib.csv"), raw)
    shutil.copy(os.path.join(repo, "res_fuel_source.csv"), raw)
    shutil.copy(os.path.join(repo, "res_model_data.csv"), raw)
    shutil.copy(os.path.join(repo, "valdez_kwh_consumption.csv"), raw)
    shutil.copy(os.path.join(repo, "ww_assumptions.csv"), raw)
    shutil.copy(os.path.join(repo, "ww_data.csv"), raw)
    shutil.copy(os.path.join(repo, "VERSION"), raw)
    shutil.copy(os.path.join(repo, "community_list.csv"), raw)
    shutil.copy(os.path.join(repo, "propane_price_estimates.csv"), raw)
    shutil.copy(os.path.join(repo, "biomass_price_estimates.csv"), raw)
    shutil.copy(os.path.join(repo, "generation_limits.csv"), raw)
  
def generate_summaries (coms, base):
    """
        generates the summaries 
    
    pre:
        coms : dictionary of run communites
        base: path to root of out put folder
    post:
        summaries are written
    """
    summaries.res_log(coms,os.path.join(base,'results'))
    summaries.com_log(coms,os.path.join(base,'results'))
    summaries.village_log(coms,os.path.join(base,'results'))
    summaries.building_log(coms,os.path.join(base,'results'))
    summaries.fuel_oil_log(coms,os.path.join(base,'results'))
    summaries.forecast_comparison_log(coms,os.path.join(base,'results'))
    
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
        
        
        
        
        
        
    
