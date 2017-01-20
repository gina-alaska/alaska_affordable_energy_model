.. _rst_tutorial:

************
CLI Commands
************


General
=======

Here is a description of the Commands for the Alaska Affordable Energy Model (AAEM) Command Line Interface (CLI). The CLI can be accessed by calling aaem. 

>>> aaem

This will display usage info, a list of commands, and options. The commands are used to perform a specific model function. Each command has it’s own subsection below.  The options listed here are general options and will be applied to any command called.

General options:
 * time (--time, -t ): will display the time elapsed for running a command
 * warn (--warn, -w): show warnings

The format of all all cli commands is. (optional info) <required info>
	
>>> aaem (general options) <command> (options) (arguments)

For example, the run command:
	
>>> aaem -t run -f Adak_Example.yaml


Setup
=====

The setup command can be used to quickly set up the structure needed to run the model and perform an initial model run using default settings. 

>>> aaem setup <path to create model directory at> <path to AAEM data repo> 

Options:
 * Dev (--dev, -d): use only the development communities
 * Force (--force, -f): force overwriting of existing directories  

Example, with dev flag:

>>> aaem setup -d ./model ./alaska_affordable_energy_model-data

Run
===

Run the model. Requires that the directory with the model info is set up with the structure that the setup or refresh command will provide.

>>> aaem run <path to model directory or script file> (list of communities) 

Options:
 * Dev (--dev, -d): use only the development communities
 * Force (--force, -f): force overwriting of existing directories  
 * Log (--log, -l): name/ path of a file to log the output from command to 
  * Use --log <log_file>
  * Example: --log OUTPUT.txt
 * Plot (--plot, -p): run the plotting functions and save results to the provided directory
  * Use: --plot <directory>
  * Ex: -p ./model/PLOTS
 * Tag (--tag, -t): tag for results directory 
  * use : -t <tag>
  * Ex: -t cool_example_results
 * Scalers (--scalers, -s): scalers to be used in running model
  * Available scalers:
   * diesel price
   * diesel price adder
   * capital costs 
   * kWh consumption
  * Use: -s <scalar string>
 * Ex: -s '{capital costs:1.1, diesel price:10}'

Example, with timing:

>>> aaem -t run ./model

Example, list of communities:

>>> aaem run ./model Adak Bethel 'Manley Hot Springs'

Example, all projects for a given community:

>>> aaem run ./model Adak*

Example, list of communities, force:

>>> aaem run -f ./model Adak Bethel 'Manley Hot Springs'

	
Example, script:
		
>>> aaem run script_file.yaml

Example, scalers:

>>> aaem run -s '{diesel price:10}' ./model 

Refresh
=======
	
regenerate(or generate) the model directory structure needed for running the model using the data in the data repo. Use a tag to name the output directory 
	
>>> aaem setup <path to (create) model directory> <path to AAEM data repo> (tag) 

Options:
 * Dev (--dev, -d): use only the development communities
 * Force (--force, -f): force overwriting of existing directories  

Example, tagged:
     
>>> aaem refresh ./ ./alaska_affordable_energy_model-data model

Compare
=======

Compare results between model runs.

>>> aaem compare <one set of results> <another set of results> (list of coms)

Example, for all:

>>> aaem compare ./model/results_A ./model/results_B

Example, for Adak:
    
>>> aaem compare ./model/results_A ./model/results_B Adak
    

List
==== 

List communities and projects that can be run

>>> aaem list <model directory>

Example:

>>> aaem list ./model

Copy
====

Copy model structure from one place to another

>>> aaem copy <source> <destination>

Options:
 * Force (--force, -f): force overwriting of existing directories  

Example:

>>> aaem copy ./model ./model__COPY

Help
====

Display help for a provided command, or list available commands 

>>> aaem help (command)

Example, with command :

>>> aaem help run






