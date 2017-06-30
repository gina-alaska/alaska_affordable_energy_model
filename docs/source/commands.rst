.. _CLI:

************
Command Line Interface (CLI) Commands
************


General
=======

Here is a description of the Commands for the Alaska Affordable Energy Model (AAEM) Command Line Interface (CLI). The CLI can be accessed by calling aaem.

.. code-block:: bash

     aaem

This will display usage info, a list of commands, and options. The commands are used to perform a specific model function. Each command has it’s own subsection below.  The options listed here are general options and will be applied to any command called.

General options:
 * time (--time, -t ): will display the time elapsed for running a command
 * warn (--warn, -w): show warnings

The format of all all cli commands is. (optional info) <required info>

.. code-block:: bash

     aaem (general options) <command> (options) (arguments)

For example, the run command:

.. code-block:: bash

     aaem -t run -f Adak_Example.yaml


Setup
=====

The setup command can be used to quickly set up the structure needed to run the model and perform an initial model run using default settings.

.. code-block:: bash

     aaem setup <path to create model directory at> <path to AAEM data repo>

Options:
 * Dev (--dev, -d): use only the development communities
 * Force (--force, -f): force overwriting of existing directories

Example, with dev flag:

.. code-block:: bash

     aaem setup -d ./model ./alaska_affordable_energy_model-data

Refresh
=======

regenerate(or generate) the model directory structure needed for running the model using the data in the data repo. Use a tag to name the output directory

.. code-block:: bash

     aaem refresh <path to (create) model directory> <path to AAEM data repo> (tag)

Options:
 * Dev (--dev, -d): use only the development communities
 * Force (--force, -f): force overwriting of existing directories
 * Make Globals (--make_globals, -g): splits the configurations generated into a global file and community files

Example, tagged:

.. code-block:: bash

     aaem refresh ./ ./alaska_affordable_energy_model-data model

Get Data
========

The Get Data command creates a directory of data files that the AAEM preprocessor needs to run, by pulling data from the API when available, and defaulting to files in the AAEM-data otherwise.

.. code-block:: bash

     aaem get-data <path to AAEM data repo> <path to create new data directory at>

Options:
 * Force (--force, -f): force overwriting of existing directories

Example:

.. code-block:: bash

     aaem get-data ./alaska_affordable_energy_model-data ./my-new-AAEM-data

Run
===

Run the AAEM. Requires that the directory with the model info is set up with the structure that the setup or refresh command will provide.
The model may also be run from a script file see :ref:`scripts`.

.. code-block:: bash

     aaem run <path to model directory or script file> (list of communities)

Options:
 * Dev (--dev, -d): use only the development communities
 * Force (--force, -f): force overwriting of existing directories
 * Log (--log, -l): name/ path of a file to log the output from command to
  * Use --log <log_file>
  * Example: --log OUTPUT.txt
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

Options (Removed in 0.27.0, should work in verions prior to that):
 * Plot (--plot, -p): run the plotting functions and save results to the provided directory
  * Use: --plot <directory>
  * Ex: -p ./model/PLOTS

Example, with timing:

.. code-block:: bash

     aaem -t run ./model

Example, list of communities:

.. code-block:: bash

     aaem run ./model Adak Bethel 'Manley Hot Springs'

Example, all projects for a given community:

.. code-block:: bash

     aaem run ./model Adak*

Example, list of communities, force:

.. code-block:: bash

     aaem run -f ./model Adak Bethel 'Manley Hot Springs'


Example, script (see :ref:`scripts` for more details):

.. code-block:: bash

     aaem run script_file.yaml

Example, scalers:

.. code-block:: bash

     aaem run -s '{diesel price:10}' ./model

Summaries
========

Creates the html summaries for model results

.. code-block:: bash

     aaem summaries <path to model> (tag)

Options:
 * Alternate output path (--alt_out, -a): Alternate output path
 * Force (--force, -f): force overwriting of existing directories

Example:

.. code-block:: bash

     aaem summaries model/m0.27.0_d0.27.0

Example, with tag:

.. code-block:: bash

     aaem summaries model/m0.27.0_d0.27.0 test_tag

Compare
=======

Compare results between model runs.

.. code-block:: bash

     aaem compare <one set of results> <another set of results> (list of coms)

Example, for all:

.. code-block:: bash

     aaem compare ./model/results_A ./model/results_B

Example, for Adak:

.. code-block:: bash

     aaem compare ./model/results_A ./model/results_B Adak


List
====

List communities and projects that can be run

.. code-block:: bash

     aaem list <model directory>

Example:

.. code-block:: bash

     aaem list ./model

Copy
====

Copy model structure from one place to another

.. code-block:: bash

     aaem copy <source> <destination>

Options:
 * Force (--force, -f): force overwriting of existing directories

Example:

.. code-block:: bash

     aaem copy ./model ./model__COPY

Help
====

Display help for a provided command, or list available commands

.. code-block:: bash

     aaem help (command)

Example, with command :

.. code-block:: bash

     aaem help run
