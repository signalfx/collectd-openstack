# Collectd OpenStack Plugin

An OpenStack [collectd](http://www.collectd.org/) plugin which users can use to send metrics from OpenStack cloud to SignalFx

## Installation

* Checkout this repository somewhere on your system accessible by collectd. The suggested location is `/usr/share/collectd/`
* Configure the plugin (see below)
* Restart collectd

## Requirements

* collectd 4.9 or later (for the Python plugin)
* Python 2.6 or later
* Python libraries from requirement.txt

## Configuration
The following are required configuration keys:

* AuthURL - Required. Keystone authentication URL/endpoint for the OpenStack cloud
* Username - Required. Username to authenticate with keystone identity
* Password - Required. Password to authenticate with keystone identity

Optional configurations keys include:

* ProjectName - Name of the Project to be monitored, default 'demo'
* ProjectDomainId - Domain to which the project belong to, 'default'
* UserDomainId - Domain to which the user belong to, 'default'
* Dimension - Add extra dimensions to your metrics


Note that multiple OpenStack projects can be configured in the same file.

```
LoadPlugin python
<Plugin python>
  ModulePath "/usr/share/collectd/collectd-openstack"

  Import openstack_metrics
  <Module openstack_metrics>
        AuthURL "http://localhost/identity/v3"
        Username "admin"
        Password "secret"
        ProjectName "demo"
        ProjectDomainId "default"
        UserDomainId "default"
    </Module>
  <Module openstack_metrics>
        AuthURL "http://localhost/identity/v3"
        Username "admin"
        Password "secret"
        ProjectName "alt_demo"
        ProjectDomainId "default"
        UserDomainId "default"
    </Module>
</Plugin>
```
