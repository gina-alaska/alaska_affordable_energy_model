import yaml
import os.path
import sys

# TODO: fix the way this is done
testdir = os.path.dirname(__file__)
srcdir = '../aaem'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))
#~ import unittest
from community_data import CommunityData
import unittest
class TestCommunityData(unittest.TestCase):
    def setUp (self):
        """ Function doc """
        
        cwd = os.path.dirname(os.getcwd())
        self.overrides_path = os.path.join(cwd,"tests","yaml", "data_override.yaml")
        self.defaults_path = os.path.join(cwd,"tests","yaml", "data_defaults.yaml")
        self.absolutes_path = os.path.join(cwd, 'aaem', "absolute_defaults.yaml")
        
        self.cd = CommunityData(os.path.join(cwd,"data","community_data_template.csv"),
                            "Manley Hot Springs")
        self.results = self.cd.read_config(os.path.join(cwd,
                                    "tests","yaml", "saved_inputs.yaml"))
    
    def test_read_config (self):
        test_data = {'community': {'consumption HF': 'ABSOLUTE DEFAULT',
                      'consumption kWh': 'ABSOLUTE DEFAULT',
                      'current year': 'ABSOLUTE DEFAULT',
                      'diesel generation efficiency': 10.802351555,
                      'diesel generator o&m': 84181,
                      'discount rate': 0.03,
                      'elec non-fuel cost': 'ABSOLUTE DEFAULT',
                      'fuel o&m': 1000,
                      'fuel repairs': 500,
                      'generation': 'ABSOLUTE DEFAULT',
                      'heating fuel preimum': 0.45,
                      'interest rate': 0.05,
                      'line losses': 'ABSOLUTE DEFAULT',
                      'name': 'ABSOLUTE DEFAULT NAME',
                      'res non-PCE elec cost': 'ABSOLUTE DEFAULT'},
                     'community buildings': {'average refit cost': 7.0,
                      'cohort_savings_multiplier': 0.26,
                      'lifetime': 'ABSOLUTE DEFAULT',
                      'start year': 'ABSOLUTE DEFAULT'},
                     'construction multipliers': {'Aleutians': 1.4,
                      'Bering Straits': 1.8,
                      'Bristol Bay': 1.25,
                      'Copper River/Chugach': 1.1,
                      'Kodiak': 1.18,
                      'Lower Yukon-Kuskokwim': 1.6,
                      'North Slope': 1.8,
                      'Northwest Arctic': 1.7,
                      'Southeast': 1.15,
                      'Yukon-Koyukuk/Upper Tanana': 1.4},
                     'forecast': {'end year': 'ABSOLUTE DEFAULT',
                      'start year': 'ABSOLUTE DEFAULT'},
                     'interties': {'cost': 'ABSOLUTE DEFAULT',
                      'cost known': 'ABSOLUTE DEFAULT',
                      'hr installed': 'ABSOLUTE DEFAULT',
                      'hr operational': 'ABSOLUTE DEFAULT',
                      'lifetime': 'ABSOLUTE DEFAULT',
                      'loss per mile': 0.001,
                      'o&m cost': 10000.0,
                      'phase': 'ABSOLUTE DEFAULT',
                      'resource certainty': 'ABSOLUTE DEFAULT',
                      'resource potential': 'ABSOLUTE DEFAULT',
                      'road needed': 'ABSOLUTE DEFAULT',
                      'start year': 'ABSOLUTE DEFAULT',
                      'transmission line cost': {False: 250000, True: 500000}},
                     'residential buildings': {'average refit cost': 11000,
                      'lifetime': 'ABSOLUTE DEFAULT',
                      'start year': 'ABSOLUTE DEFAULT'},
                     'water wastewater': {'audit cost': 10000,
                      'energy use known': 'ABSOLUTE DEFAULT',
                      'heat recovery multiplier': {False: 1.0, True: 0.5},
                      'lifetime': 'ABSOLUTE DEFAULT',
                      'start year': 'ABSOLUTE DEFAULT',
                      'system type': 'ABSOLUTE DEFAULT'}}

        self.assertEqual(test_data, self.cd.read_config(self.absolutes_path))
       
    def test_validate_config (self):
        """ Function doc """
        self.assertTrue(self.cd.validate_config({'community':{'name':'manley'},
                                                'forecast':{'start year':2010,
                                                            'end year':2100}}))
        self.assertFalse(self.cd.validate_config({'community':{'name':'manley'},
                                                'BUG':{'start year':2010,
                                                            'end year':2100}}))
        self.assertFalse(self.cd.validate_config({'community':{'name':'manley'},
                                                'forecast':{'start year':2010,
                                                            'BUG':2100}}))
        
    
    def test_glom_config_files(self):
        cwd = os.path.dirname(os.getcwd())
        self.cd.client_inputs = self.cd.read_config(os.path.join(cwd,
                                                    self.overrides_path))
        self.cd.client_defaults = self.cd.read_config(os.path.join(cwd,
                                                            self.defaults_path))
        self.cd.absolute_defaults = self.cd.read_config(self.absolutes_path)
        self.cd.glom_config_files()
        self.assertEqual(self.results, self.cd.model_inputs)
        

    def test_load_input (self):
        defaults = os.path.join("test_case", "data_defaults.yaml")
        overrides = os.path.join("test_case", "data_override.yaml")
        self.cd.load_input(overrides, defaults)
        self.assertEqual(self.results, self.cd.model_inputs)
        

if __name__ == '__main__':
    unittest.main()
