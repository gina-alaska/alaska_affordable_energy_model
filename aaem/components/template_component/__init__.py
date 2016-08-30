"""
__init__.py

    model component for findng economic benefits related to improving 
<ADD COMP NAME/DESCRIPTION HERE> in a community
"""
## steps for using
### 1) copy contents of directory into a component_name a directory 
###     and go through each file folloing the commented instructions
### 2) add the component to __init__.py in this aaem/components directory
### 3) add/change content to template function

##  Do a find on replace on all files for <ADD COMP NAME/DESCRIPTION HERE> 
## add the name or a description of the component
from preprocessing import *
from config import *
from inputs import *
from component import *
from outputs import *

## DO a find and replace on ComponentName with the component name
component = ComponentName
