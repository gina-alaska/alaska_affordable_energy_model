# alaska_affordable_energy_model
Alaska Energy Authority - Alaska Affordable Energy Model
Created by University of Alaska Fairbanks/GINA

# extra python libraries used:
numpy, scipy, pandas: info on those here: http://www.scipy.org/

pyymal

# model files:
    aea_assumptions.py
        a place for the assumptions the Alaska energy association(administration?)(AEA) has made

    components/annual_savings.py
        Contains base class for each of the model components(tabs in the spreadsheet
    on basecamp) that have a financial forecasting section.

    components/community_buildigns.py
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

    components/interties.py
        Python version of interties tab.

    components/residential_buildings.py
         python version of the eff(res) tab.

    components/wastewater.py
        python version of the eff(w&ww) tab.

    README
        this file


# python examples:
from the aaem/ directory

    $ python
    Python 2.7.9 (default, Apr  2 2015, 15:33:21)
    [GCC 4.9.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.

the individual component test don't take any arguments and return the model components used

    >>> import components.wastewater as wastewater
    >>> ww, fc = wastewater.test()

    47797.0
    61254.0
    0.78
    13457.0
    >>> ww.benefit_cost_ratio
    0.78031511335568371
    >>> fc.www_HF
    array([    0.        ,   891.21513076,   929.59932095,   969.63669902,
        1011.39846696,  1054.95889336,  1100.39544556,  1147.78892734,
        1197.2236227 ,  1248.78744567,  1302.57209673,  1358.67322582,
        1417.1906025 ,  1478.22829334,  1541.89484701,  1608.30348732,
        1608.30348732,  1608.30348732,  1608.30348732,  1608.30348732,
        1608.30348732,  1608.30348732,  1608.30348732,  1608.30348732,
        1608.30348732,  1608.30348732,  1608.30348732])



the test in driver take the community name as an input, There is only data for manley right now. A pandas DataFrame(just a mock of the table in the forecast tab) is returned along with the model components as a tuple

    >>> df, model_componets = driver.test("Manley Hot Springs")
    >>> print df
       HH     avg. kW       com HF    kWh consumed  kWh generation  \
       2014   56   50.719736      0.00000   390543.996100          444000   
       2015   58   52.904210  41716.39827   407364.530791          463000   
       2016   61   55.182768  41716.39827   424909.517503          483000   
       ...
