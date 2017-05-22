"""
deffinitions
------------

defitions of common terms used in the model
"""

## some defintions
NPV_BENEFITS = "Net present value of saving ($) from improvements."
NPV_COSTS = "Net present value of capital and operating cost ($) for improvments."
NPV_NET_BENEFITS = "Net present value of savings minus costs ($) from improvements."
NPV_BC_RATIO = "Ratio of NPV benefits to NPV costs. A value greater than 1 indcates the project is cost effective."
IRR = 'Internal rate of return.'
NOTES = 'Notes on component execution.'
LCOE = 'The average the unit-cost of energy over the lifetime of an asset.'
BREAK_EVEN_COST_HF = "Average heating fuel price where project would become cost effective."
BREAK_EVEN_COST_DIESEL = "Average diesel price where project would become cost effective."
PRICE_HF = "Heating fuel price in the community during the first year of project operation."
PRICE_ELECTRICITY = "Electricity price in the community during the first year of project operation."
PRICE_DIESEL = "Diesel fuel price in the community during the first year of project operation."
FUEL_DISPLACED = "Fuel that would be displaced by improvments." 
COMMUNITY = "Name of community/project."
START_YEAR = "Year the project is projected to start operation."
PHASE = "Current phase of project."
DIESEL_LOAD = "Current average load from diesel generation in community in kilowatts."
GEN_EFF = 'Estimated efficiency of diesel generator in killowatt-hours per gallon.'
HR_OP = "Boolean indcating if heat recovey is operational in community."
PREMIUM = "Extra cost of heating fuel above utility diesel"


ENABLED = '[bool] Boolean Indicating if the component should be run'
LIFETIME = '[int] lifetime of the load for the project'
START_YEAR_WITH_TYPE = '[int] Operation start year for the project'
