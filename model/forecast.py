"""
forecast.py
Ross Spicer
created: 2015/09/18

    mock up of for cast tab
"""
import numpy as np
# TODO: this is for manley, but I'm not sure where it comes from
fossil_fuel_gen_displaced = [395674.849879193,418138.515848389,441877.512531502,
                             466964.244336258,493475.226289067,521491.317407356,
                             551097.967321171,582385.476896231,615449.273653346,
                             650390.202824239,687314.83493149,726335.790830729,
                             767572.085206463,811149.489569216,857200.915861106,
                             905866.821839895,957295.639477916,1011644.22768251,
                             1069078.3507188,1129773.18379393,1193913.84734495,
                             0.0,0.0,0.0] # extra zeros 
fossil_fuel_gen_displaced = np.array(fossil_fuel_gen_displaced)


class Forecast (object):
    """ Class doc """
    
    def __init__ (self, start_year):
        """ Class initialiser """
        self.start_year = start_year
        self.ff_gen_displaced = fossil_fuel_gen_displaced
        
    def get_fossil_fuel_generation_displaced (self, start, end):
        """
        """
        return self.ff_gen_displaced[start-self.start_year:end-self.start_year]


def test (start_year = 2015):
    """ Function doc """
    fc = Forecast(start_year)
    return fc
