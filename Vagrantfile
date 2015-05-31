#-*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "mast3rof0/awscli"
  config.vm.hostname = "awscli"
  config.vm.network "private_network", ip: "172.28.128.199"
  config.vm.provider "virtualbox" do |vb|
    vb.name = "awscli"
  end
  config.vm.provision "shell", inline: "sudo mkdir /vagrant/.aws"
  config.vm.provision "shell", inline: "sudo chown root:root /vagrant/.aws"
end
