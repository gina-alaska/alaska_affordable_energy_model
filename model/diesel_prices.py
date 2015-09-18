"""
diesel_prices.py
Ross Spicer
created 2015/09/17

    for calculating diesel price projections 
"""
import numpy as np
#  TODO: this needs to be made not static


co2_allowance_cost = [0.4731808371,0.4873762622,0.5019975501,0.5170574766,
                      0.5325692009,0.5485462769,0.5650026652,0.5819527452,
                      0.5994113275,0.6173936674,0.6359154774,0.6549929417,
                      0.67464273,0.6948820119,0.7157284722,0.7372003264,
                      0.7593163362,0.7820958262,0.805558701,0.8297254621,
                      0.8546172259,0.8802557427,0.906663415,0.9338633174,
                      0.961879217,0.9907355935,1.0204576613,1.0510713911,
                      1.0826035328,1.1150816388,1.148534088,1.1829901106,
                      1.218479814,1.2550342084,1.2926852346,1.3314657917,
                      1.3714097654,1.4125520584,1.4549286201,1.4985764787,
                      1.5435337731,1.5898397863,1.6375349799,1.6866610293,
                      1.7372608601,1.789378686,1.8430600465,1.8983518479,
                      1.9553024034,2.0139614755,2.0743803197,2.1366117293,
                      2.2007100812,2.2667313836,2.3347333251,2.4047753249,
                      2.4769185846,2.5512261422,2.6277629265,2.7065958142,
                      2.7877936887,2.7877936887]
co2_allowance_cost = np.array(co2_allowance_cost)


manley_price_per_gal = [2.6551872278,3.1224832059,3.2868240967,3.2988439943,
                        3.3548353302,3.4111187308,3.4873851625,3.5691384113,
                        3.6538119975,3.7402810267,3.8271557775,3.9197045121,
                        4.0145168849,4.1116492907,4.2111592179,4.3131053947,
                        4.4175486539,4.5245507326,4.6340259638,4.7416270426,
                        4.8548324203,4.971160883,5.0852484008,5.207910448,
                        5.3402464275,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299,5.4636003299,5.4636003299,
                        5.4636003299,5.4636003299]
manley_price_per_gal = np.array(manley_price_per_gal)




gallons_per_barrel = 42 #gal/barrel - from Diesel fuel price tab 

class DieselProjections (object):
    """ 
    This class Projects diesel fuel prices
    """
    
    def __init__ (self, start_year):
        """
        create the projected values
        Pre:
            start_year is the first year of the projection
        Post:
            self.projected_prices will contain the projected prices 
        """
        self.start_year = start_year
        self.calc_projected_prices()

    # TODO: calculate correctly 
    def calc_projected_prices (self):
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
        self.projected_prices = manley_price_per_gal
        
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


start_year = 2015

def test ():
    """
    test the class using the manley data
    pre: none
    post: retuns the object for further testing
    """
    pp = DieselProjections(start_year)
    return pp

    
