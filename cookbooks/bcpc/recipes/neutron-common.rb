#
# Cookbook Name:: bcpc
# Recipe:: neutron-common
#
# Copyright 2017, Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

return unless node['bcpc']['enabled']['neutron']

include_recipe "bcpc::openstack"

ruby_block "initialize-neutron-config" do
  block do
    make_config('mysql-neutron-user', "neutron")
    make_config('mysql-neutron-password', secure_password)
    make_config('keystone-neutron-password', secure_password)
  end
end

package 'neutron-common' do
  action :upgrade
end

%w(etc/neutron /etc/neutron/plugins/ml2).each do |d|
  directory d do
    owner 'neutron'
    group 'neutron'
    mode 00700
    recursive true
  end
end

template '/etc/neutron/neutron.conf' do
  source 'neutron/neutron.conf.erb'
  owner 'neutron'
  group 'neutron'
  mode 00600
  variables(
    lazy {
      {
        :headnodes => get_head_nodes,
        :servers   => get_all_nodes,
        :partials  => {
          'keystone/keystone_authtoken.snippet.erb' => {
            'variables' => {
              username: node['bcpc']['neutron']['user'],
              password: get_config('keystone-neutron-password')
            }
          }
        }
      }
    }
  )
end

template '/etc/neutron/plugins/ml2/ml2_conf.ini' do
  source 'neutron/neutron.ml2_conf.ini.erb'
  owner 'neutron'
  group 'neutron'
  mode 00600
end

link '/etc/neutron/plugin.ini' do
  to '/etc/neutron/plugins/ml2/ml2_conf.ini'
end
