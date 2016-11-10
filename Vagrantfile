# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box_url = "https://s3-us-west-2.amazonaws.com/gina-vagrant-boxes/win7x64-pro.box"
  config.vm.box = 'win7x64-pro'
  config.vm.box_check_update = false

  config.vm.synced_folder ".", "/Users/vagrant/Desktop/aaem"
  config.vm.synced_folder "../alaska_affordable_energy_model-data", "/data"

  config.vm.provider "virtualbox" do |vb|
    vb.gui = true
    vb.memory = "1024"
  end

end
