# alaska_affordable_energy_model
Alaska Energy Authority - Alaska Affordable Energy Model 


# extra python libraries used:
numpy, scipy, pandas
info on those here: http://www.scipy.org/

# python files:
    aea_assumptions.py 
        a place for the assumptions the Alaska energy association(administration?)(AEA) has made
    
    annual_savings.py
        Contains base class for each of the model components(tabs in the spreadsheet 
    on basecamp) that have a financial forecasting section. 
    
    community_buildigns.py
        python version of the eff(com) tab.
    
    community_data.py 
        python version of community data tab. This is the inputs for the model, 
    currently loaded from a .csv file
    
    diesel_prices.py
        python version of Diesel Fuel Prices tab.
        
    driver.py
        contains a function to test the model components together. 
    
    forecast.py
        Python version of forecast tab. The object defined here is passed
    as input to model components that use/update its members
    
    interties.py
        Python version of interties tab.
        
    residential_buildings.py
         python version of the eff(res) tab.
         
    wastewater.py
        python version of the eff(w&ww) tab.
        
    com_benchmark_data.csv
        data on commercial buildings pulled from spread sheet. This file is 
    read in community_data.py
    
    comunity_data_template.csv
        prototype template of the data needed for the CommunityData class in
    community_data.py. I think the plan is for this information to eventually 
    come for a database with a name I cannot recall.  
    
    README 
        this file
        
    res_data.csv
        data on residential buildings pulled from spread sheet. This file is 
    read in community_data.py
    

# python examples:
-- from the model/ directory 

$ python
Python 2.7.9 (default, Apr  2 2015, 15:33:21) 
[GCC 4.9.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.

-- the individual component test don't take any arguments and return the model
-- components used
'>>> import wastewater
'>>> ww, fc = wastewater.test()

47797.0
61254.0
0.78
-13457.0
'>>> ww.benefit_cost_ratio 
0.78031511335568371
'>>> fc.www_HF
array([    0.        ,   891.21513076,   929.59932095,   969.63669902,
        1011.39846696,  1054.95889336,  1100.39544556,  1147.78892734,
        1197.2236227 ,  1248.78744567,  1302.57209673,  1358.67322582,
        1417.1906025 ,  1478.22829334,  1541.89484701,  1608.30348732,
        1608.30348732,  1608.30348732,  1608.30348732,  1608.30348732,
        1608.30348732,  1608.30348732,  1608.30348732,  1608.30348732,
        1608.30348732,  1608.30348732,  1608.30348732])
        
-- the test in driver take the community name as an input, There is only
-- data for manley right now. A pandas DataFrame(just a mock of the table in the forecast tab) 
-- is returned along with the model components as a tuple 
'>>> df, model_componets = driver.test("Manley Hot Springs")




