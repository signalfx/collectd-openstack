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
    custom_dimensions = {}

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
            elif node.key.lower() == 'dimension':
                if len(node.values) == 2:
                    custom_dimensions.update({node.values[0]: node.values[1]})
                else:
                    collectd.warning("WARNING: Check configuration setting for %s" % node.key)
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

    if testing:
        return plugin_conf

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
        OPENSTACK_CLIENT['custdims'] = custom_dimensions

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
        serverCounterMetrics = ['cpu0_time', 'cpu1_time', 'rx', 'rx_packets', 'tx', 'tx_packets']

        for hypervisor in hypervisorMetrics:
            metrics, dims, props = hypervisorMetrics[hypervisor]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props, data['custdims'])

        for server in serverMetrics:
            metrics, dims, props = serverMetrics[server]
            for (metric, value) in metrics:
                if metric.split(".")[3] in serverCounterMetrics:
                    dispatch_values(metric, value, dims, props, data['custdims'], 'counter')
                else:
                    dispatch_values(metric, value, dims, props, data['custdims'])

        for limit in limitMetrics:
            metrics, dims, props = limitMetrics[limit]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props, data['custdims'])

        for storage in blockStorageMetrics:
            metrics, dims, props = blockStorageMetrics[storage]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props, data['custdims'])

        for network in networkMetrics:
            metrics, dims, props = networkMetrics[network]
            for (metric, value) in metrics:
                dispatch_values(metric, value, dims, props, data['custdims'])

    except Exception as e:
        collectd.error(
            "Failed to fetch Openstack metrics due to {0}".format(e)
        )


def prepare_dims(dims, custdims):
    if bool(custdims) is False:
        return dims

    for (key, val) in custdims.iteritems():
        dims[key] = val

    return dims


def _formatDimsForSignalFx(dims):
    formatted = ",".join(["{0}={1}".format(d, dims[d]) for d in dims])
    return "[{0}]".format(formatted) if formatted != "" else ""


def dispatch_values(metric, value, dims, props, custdims, metric_type="gauge"):
    dims = prepare_dims(dims, custdims)
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
