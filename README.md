# :warning: This plugin is no longer maintained.

>ℹ️&nbsp;&nbsp;SignalFx was acquired by Splunk in October 2019. See [Splunk SignalFx](https://www.splunk.com/en_us/investor-relations/acquisitions/signalfx.html) for more information.

# Collectd OpenStack Plugin

An OpenStack [collectd](http://www.collectd.org/) plugin which users can use to send metrics from OpenStack cloud to SignalFx

## Installation

* Checkout this repository somewhere on your system accessible by collectd. The suggested location is `/usr/share/collectd/`
* Configure the plugin (see below)
* Restart collectd

## Requirements

* collectd 4.9 or later (for the Python plugin)
* Python 2.7 or later
* Python libraries from requirements.txt (requirements-python2.txt for Python 2.7).

## Configuration
The following are required configuration keys:

* AuthURL - Required. Keystone authentication URL/endpoint for the OpenStack cloud
* Username - Required. Username to authenticate with keystone identity
* Password - Required. Password to authenticate with keystone identity

Optional configurations keys include:

* Interval - The number of seconds to wait between collections with default of 10.
* ProjectName - Name of the Project to be monitored with default of "demo".
* ProjectDomainId - Domain to which the project belong to with default of "default".
* UserDomainId - Domain to which the user belong to with default of "default".
* RegionName - The region name for URL discovery, defaults to the first region if multiple regions are available.
* Dimension - Dimensions name and value to add to your metrics.
* SSLVerify - Whether to validate SSL certificates. True by default
* HTTPTimeout - The keystone http session timeout, in seconds, for all requests. None by default.
* RequestBatchSize - The maximum number of concurrent requests for server metrics. 5 by default.
* QueryServerMetrics - Whether to query for Nova metrics. True by default.
* QueryHypervisorMetrics - Whether to query for hypervisor metrics. True by default, disable for Openstack-on-Openstack environments.
* NovaListServersSearchOpts - A yaml representation of a search options dictionary for Nova servers to query. Expanded to query parameters for https://docs.openstack.org/api-ref/compute/#list-servers.

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
        Interval 30
        ProjectName "demo"
        ProjectDomainId "default"
        UserDomainId "default"
        HTTPTimeout 10.0
        RequestBatchSize 20
        NovaListServersSearchOpts "{ all_tenants: 'TRUE', status: 'ACTIVE' }" 
    </Module>
  <Module openstack_metrics>
        AuthURL "http://localhost/identity/v3"
        Username "admin"
        Password "secret"
        ProjectName "alt_demo"
        ProjectDomainId "default"
        UserDomainId "default"
        SSLVerify False
        QueryServerMetrics False
    </Module>
</Plugin>
```
