"""
diesel_prices.py
Ross Spicer
created 2015/09/17

    for calculating diesel price projections 
"""
import numpy as np


# price per barrel projections 2013 - 2075
# TODO: import from source 
price_per_barrel = [103.35,97.3619959996,93.9353836392,90.4595627757,
                    89.3641723069,89.5034893086,90.7826131871,92.2338130483,
                    93.9332662162,95.6567950886,97.5098229738,99.184694254,
                    100.6745135781,101.8035021479,103.3944705795,104.5588989267,
                    105.8184503032,106.7733064245,108.2029534557,109.8851625292,
                    111.5104657561,113.0114485397,114.5002261173,115.8513077399,
                    117.4690335807,118.9695309514,121.0899407041,123.4857347068,
                    124.2092839336,124.9370727067,125.669125867,126.4054684014,
                    127.1461254428,127.8911222716,128.6404843162,129.394237154,
                    130.1524065123,130.9150182692,131.6820984544,132.45367325,
                    133.2297689917,134.0104121694,134.7956294282,135.5854475694,
                    136.3798935512,137.17899449,137.9827776609,138.7912704987,
                    139.6045005993,140.42249572,141.2452837809,142.0728928655,
                    142.9053512222,143.7426872645,144.5849295727,145.4321068944,
                    146.2842481457,147.1413824122,148.0035389498,148.8707471858,
                    149.7430367201,150.6204373259,151.5029789509] 
price_per_barrel = np.array(price_per_barrel)


# CO2-equivalent allowance cost 2013 - 2075
# TODO: import from source 
co2_allowance_cost = [0.4105414619,0.4228577058,0.435543437,0.4486097401,
                      0.4620680323,0.4759300732,0.4902079754,0.5049142147,
                      0.5200616411,0.5356634904,0.5517333951,0.5682853969,
                      0.5853339589,0.6028939776,0.6209807969,0.6396102209,
                      0.6587985275,0.6785624833,0.6989193578,0.7198869385,
                      0.7414835467,0.7637280531,0.7866398947,0.8102390915,
                      0.8345462643,0.8595826522,0.8853701318,0.9119312357,
                      0.9392891728,0.967467848,0.9964918834,1.0263866399,
                      1.0571782391,1.0888935863,1.1215603939,1.1552072057,
                      1.1898634219,1.2255593245,1.2623261043,1.3001958874,
                      1.339201764,1.3793778169,1.4207591514,1.463381926,
                      1.5072833838,1.5525018853,1.5990769418,1.6470492501,
                      1.6964607276,1.7473545494,1.7997751859,1.8537684415,
                      1.9093814947,1.9666629396,2.0256628277,2.0864327126,
                      2.149025694,2.2134964648,2.2799013587,2.3482983995,
                      2.4187473515,2.491309772,2.5660490652
]
co2_allowance_cost = np.array(co2_allowance_cost)

# constants 
# TODO: move to assumptions/constants file
gallons_per_barrel = 42 #gal/barrel - from Diesel fuel price tab 


# TODO: rework class interface, the intercept, slope and base_price
#       all come from the evaluation model
class DieselProjections (object):
    """ 
    This class Projects diesel fuel prices
    """
    
    def __init__ (self, slope, intercept, base_price, 
                                    start_year, urban = False):
        """
        create the projected values
        Pre:
            this will all change, but for now slope and intercerpt should 
        be numbers. 
            Base_price should be a dollar value(float) in (price/gal) for the
        first year of the projection. 
            start_year is the first year of the projection
            urban is a ture if it is an urban community/ false other wise
        Post:
            self.projected_prices will contain the projected prices 
        """
        self.slope = slope
        self.intercept = intercept
        self.base_price = base_price
        self.start_year = start_year
        self.calc_projected_prices(urban)

    def calc_projected_prices (self, urban = False):
        """
        calculate the projected prices
        
        pre:
            this will all change, but for now self.slope and self.intercerpt 
        should be numbers. 
            self.base_price should be a dollar value(float) in (price/gal) 
        for the first year of the projection. 
            urban is a ture if it is an urban community/ false other wise
        post:
            self.projected_prices will contain the projected prices 
        """
        price_per_gallon = price_per_barrel/gallons_per_barrel 
        if not urban:
            price_per_gallon = np.roll(price_per_gallon,1)
            
        self.projected_prices = (self.slope * price_per_gallon) + \
                                self.intercept + co2_allowance_cost
        self.projected_prices[0] = self.base_price

        
    def get_projected_prices (self, start_year, end_year):
        """
        get the projected prices for a given range of years
        pre:
            start_year < end_year where both are  > self.start year but less 
        than the end year of the projection
        pre: 
            returns the prjectied prices as an array 
        """
        return self.projected_prices[start_year-self.start_year:
                                     end_year-self.start_year]


# manley test data
# TODO: Does this fold into community_data.py
manley_slope = 1.475
manley_intercept = 0.548
manley_2013_price = 4.03
start_year = 2013

def test ():
    """
    test the class using the manley data
    pre: none
    post: retuns the object for further testing
    """
    pp = DieselProjections(manley_slope,manley_intercept, manley_2013_price,
                                                                    start_year)
    return pp

    
