#!/usr/bin/env ruby

require 'clamp'
require 'colorize'

Clamp do
  subcommand 'setup', "Set up directory for running AAEM Models" do
    parameter "[DIRECTORY]", "directory to store model input and output", default: Dir.getwd

    def execute
      puts "Creating workspace #{directory}"
      puts "Fetching input data from api..."
      sleep 0.5
      puts "Executing initial model run..."
      sleep 1.3
    end
  end

  subcommand 'list', "List available communtities" do
    def execute
      # Read and parse some sort of thing that contains all community names
      puts "No communtities are available"
    end
  end

  subcommand 'run', "Run model" do
    parameter "COMMUNITY ...", "List of communities to run", default: ['all'], attribute_name: :communities
    def execute

      communities.each do |community|
        puts "Validating existance of #{community} ..."
        puts "Loading configuration for #{community} ..."
      end
      puts "Loading global configuration"
      communities.each do |community|
        puts "Executing model run for #{community}.."
        sleep(rand * 2)
        puts "Saving output for #{community} to output/aaem-#{Time.now.strftime('%Y%m%d%H%M%S%L%z')}/#{community}.csv"
      end
    end
  end

  subcommand 'validate', "Validate output of previous model runs" do
    parameter "[MODEL RUN]", "directory containing the output of previous run", attribute_name: :directory
    def execute
      communities = rand(10) + 1
      puts "Loading input and configuration from #{directory}".blue.on_red
      puts "Found #{communities} communties"
      communities.times do
        name = ('a'..'z').to_a.sample(rand(8)+4).join
        puts "Executing model run for #{name}"
        sleep(rand * 2)
        puts "Comparing output to exsting run"
        sleep(rand)
        if(rand(4) == 0)
          puts "The model outputs are different: ".colorize(:red)
          puts "   ... diff ..."
        else
          puts "Outputs are identical ".colorize(:green)
        end
      end
    end
  end

  subcommand 'compare', "Compare two model runs" do
    parameter "[FIRST MODEL OUTPUT]", 'directory containing output of first model run you wish to compare', attribute_name: :d1
    parameter "[SECOND MODEL OUTPUT]", 'directory containing output of second model run you wish to compare', attribute_name: :d2

    def execute
      puts "Difference between #{d1} and #{d2}".colorize(:green)
      puts "   ...  diff  ..."
    end
  end

  subcommand 'export', "Export model run to share" do
    parameter "[MODEL RUN]", "directory containing the output of previous run", attribute_name: :directory

    def execute
      puts "Exporting #{directory} as zip file 'foo.zip' "
    end
  end

end