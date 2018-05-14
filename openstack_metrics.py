import collectd
from NovaMetrics import NovaMetrics
from CinderMetrics import CinderMetrics
from NeutronMetrics import NeutronMetrics


def config_callback(conf):
    """Receive configuration block"""
    project_name = 'demo'
    project_domainid = 'default'
    user_domainid = 'default'
    interval = 10
    testing = False
    OPENSTACK_CLIENT = {}
    plugin_conf = {}

    required_keys = frozenset(('authurl', 'username', 'password'))

    for node in conf.children:
        try:
            if node.key.lower() in required_keys:
                plugin_conf[node.key.lower()] = node.values[0]
            elif node.key.lower() == "projectname":
                project_name = node.values[0]
            elif node.key.lower() == "projectdomainid":
                project_domainid = node.values[0]
            elif node.key.lower() == "userdomainid":
                user_domainid = node.values[0]
            elif node.key.lower() == "interval":
                interval = node.values[0]
        except Exception as e:
            collectd.error(
                "Failed to load the configuration {0} due to {1}".format(
                    node.key, e
                )
            )
            raise e

    for key in required_keys:
        try:
            val = plugin_conf[key]
        except KeyError:
            raise KeyError("Missing required config setting: %s" % key)

    try:
        novametrics = NovaMetrics(
            plugin_conf['authurl'],
            plugin_conf['username'],
            plugin_conf['password'],
            project_name,
            project_domainid,
            user_domainid
        )
        OPENSTACK_CLIENT['nova'] = novametrics

        cindermetrics = CinderMetrics(
            plugin_conf['authurl'],
            plugin_conf['username'],
            plugin_conf['password'],
            project_name,
            project_domainid,
            user_domainid
        )
        OPENSTACK_CLIENT['cinder'] = cindermetrics

        neutronmetrics = NeutronMetrics(
            plugin_conf['authurl'],
            plugin_conf['username'],
            plugin_conf['password'],
            project_name,
            project_domainid,
            user_domainid
        )
        OPENSTACK_CLIENT['neutron'] = neutronmetrics

    except Exception as e:
        collectd.error(
            "Failed to authenticate Openstack client due to {0}".format(e)
        )

    collectd.register_read(read_callback, interval, data=OPENSTACK_CLIENT, name=project_name)


def read_callback(data):
    try:
        hypervisorMetrics = data['nova'].collect_hypervisor_metrics()
        serverMetrics = data['nova'].collect_server_metrics()
        limitMetrics = data['nova'].collect_limit_metrics()
        blockStorageMetrics = data['cinder'].collect_cinder_metrics()
        networkMetrics = data['neutron'].collect_neutron_metrics()

        for hypervisor in hypervisorMetrics:
            metrics, dims, props = hypervisorMetrics[hypervisor]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props)

        for server in serverMetrics:
            metrics, dims, props = serverMetrics[server]
            for (metric, value) in metrics:
                if metric.split(".")[3] in ('rx', 'rx_drop', 'rx_packets', 'tx', 'tx_drop', 'tx_packets'):
                    dispatch_values(metric, value, dims, props, 'counter')
                else:
                    dispatch_values(metric, value, dims, props)

        for limit in limitMetrics:
            metrics, dims, props = limitMetrics[limit]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props)

        for storage in blockStorageMetrics:
            metrics, dims, props = blockStorageMetrics[storage]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props)

        for network in networkMetrics:
            metrics, dims, props = networkMetrics[network]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props)

    except Exception as e:
        collectd.error(
            "Failed to fetch Openstack metrics due to {0}".format(e)
        )


def _formatDimsForSignalFx(dims):
    formatted = ",".join(["{0}={1}".format(d, dims[d]) for d in dims])
    return "[{0}]".format(formatted) if formatted != "" else ""


def dispatch_values(metric, value, dims, props, metric_type="gauge"):
    val = collectd.Values(type=metric_type)
    val.type_instance = "{0}{1}".format(metric, _formatDimsForSignalFx(dims))
    val.plugin = 'openstack'
    val.plugin_instance = _formatDimsForSignalFx(props)
    val.values = [value]
    val.dispatch()


if __name__ == "__main__":
    # run standalone
    pass
else:
    collectd.register_config(config_callback)
