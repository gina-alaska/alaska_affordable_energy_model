"""
diesel_prices.py
Ross Spicer
created 2015/09/17

    for calculating diesel price projections 
"""
import numpy as np
from pandas import read_csv
import os.path

class DieselProjections (object):
    """ 
    This class Projects diesel fuel prices
    """
    
    def __init__ (self, community, data_dir):
        """
        create the projected values
        Pre:
            comminity is a valid community string
            diesel_fuel_prices.csv exists in the data_dir
        Post:
            self.projected_prices will contain the projected prices, and 
        the start year is configred based off of it 
        """
        df = read_csv(os.path.join(data_dir,"diesel_fuel_prices.csv"), 
                        index_col=3, comment="#", header=1)
        
        # 3 is the first column that has a year as the name/index
        self.start_year = int(df.keys()[3])
        try:
            self.projected_prices = np.array(df.T[community][3:].values, 
                                                            dtype = np.float64)
        except KeyError:
            self.projected_prices = np.array(df.mean()[3:].values, 
                                                            dtype = np.float64)
            self.msg = "average used"
 
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


    
