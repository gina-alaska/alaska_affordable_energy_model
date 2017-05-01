"""
diesel_prices.py
Ross Spicer
created 2015/09/17

    for calculating diesel price projections
"""
import numpy as np
from pandas import DataFrame
import os.path

class DieselProjections (object):
    """
    This class Projects diesel fuel prices
    """

    def __init__ (self, diesel_prices, diesel_price_scaler = 1.0, adder = 0):
        """
        create the projected values
        Pre:
            comminity is a valid community string (ie. Adak, Manley_Hot_Springs)
            diesel_prices_community.csv exists in the data_dir, must have a 
            single data row
        Post:
            self.projected_prices will contain the projected prices, and
        the start year is configred based off of it
        """
        df = diesel_prices
        self.start_year = int(df.index[0])
        self.projected_prices = df * diesel_price_scaler + adder
        self.projected_prices.index.name = 'year'

    def get_projected_prices (self, start_year, end_year):
        """
        get the projected prices for a given range of years
        pre:
            start_year < end_year where both are  > self.start year but less
        than the end year of the projection
        pre:
            returns the prjectied prices as an array
        """
        prices = self.projected_prices.ix[start_year:end_year]
        if prices.index[-1] < end_year:
            
            # exta minus 1 is needed for proper range
            values = [float(prices.ix[prices.index[-1]]) \
                for i in range(end_year - prices.index[-1] - 1)] 
            
            #~ print range(prices.index[-1] + 1, end_year +1)
            pa = DataFrame(
                values, 
                index = range(prices.index[-1] + 1, end_year),
                columns = prices.columns)
            
            prices = prices.append ( pa )
    
        return prices.values.T[0]



def test ():
    """
    test the class using the manley data
    pre: none
    post: retuns the object for further testing
    """
    pp = DieselProjections("Manley Hot Springs")
    return pp

import unittest
class TestDieselProjections(unittest.TestCase):
    """
    uint tests for DieselProjections
    """
    def test_object_creation (self):
        pp = DieselProjections("Manley Hot Springs")
        self.assertEqual(pp.projected_prices.dtype,np.float64)
        self.assertTrue(len(pp.projected_prices) > 0 )

    def test_get_projected_prices (self):
        pp = DieselProjections("Manley Hot Springs").get_projected_prices(2015,
                                                                          2040)
        self.assertEqual(pp.dtype,np.float64)
        self.assertTrue(len(pp) == 2040-2015 )


#run unit tests
if __name__ == '__main__':
    unittest.main()
