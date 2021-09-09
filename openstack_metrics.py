import yaml

from CinderMetrics import CinderMetrics
from NeutronMetrics import NeutronMetrics
from NovaMetrics import NovaMetrics

import collectd

COUNTER_METRICS = set(tuple("cpu{0}_time".format(n) for n in range(32)) + ("rx", "rx_packets", "tx", "tx_packets"))


def config_callback(conf):
    """Receive configuration block"""
    project_name = "demo"
    project_domainid = "default"
    user_domainid = "default"
    region_name = None
    interval = 10
    testing = False
    ssl_verify = True
    OPENSTACK_CLIENT = {}
    plugin_conf = {}
    custom_dimensions = {}
    http_timeout = None
    request_batch_size = 5
    nova_list_servers_search_opts = {}

    query_server_metrics = True

    required_keys = frozenset(("authurl", "username", "password"))

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
            elif node.key.lower() == "regionname":
                if node.values[0]:
                    region_name = node.values[0]
            elif node.key.lower() == "dimension":
                if len(node.values) == 2:
                    custom_dimensions.update({node.values[0]: node.values[1]})
                else:
                    collectd.warning("WARNING: Check configuration setting for %s" % node.key)
            elif node.key.lower() == "interval":
                interval = node.values[0]
            elif node.key.lower() == "sslverify":
                ssl_verify = node.values[0]
            elif node.key.lower() == "httptimeout":
                http_timeout = node.values[0]
            elif node.key.lower() == "requestbatchsize":
                request_batch_size = int(node.values[0])
            elif node.key.lower() == "queryservermetrics":
                query_server_metrics = node.values[0]
            elif node.key.lower() == "novalistserverssearchopts":
                nova_list_servers_search_opts = yaml.load(node.values[0], Loader=yaml.FullLoader)
                if not isinstance(nova_list_servers_search_opts, dict):
                    raise TypeError("NovaListSeverSearchOpts must be a string representation of yaml mapping. Received {0}.".format(node.values[0]))
            elif node.key.lower() == "testing":
                testing = node.values[0]
        except Exception as e:
            collectd.error("Failed to load the configuration {0} due to {1}".format(node.key, e))
            raise e

    OPENSTACK_CLIENT["query_server_metrics"] = query_server_metrics

    for key in required_keys:
        try:
            plugin_conf[key]
        except KeyError:
            raise KeyError("Missing required config setting: %s" % key)

    try:
        novametrics = NovaMetrics(
            auth_url=plugin_conf["authurl"],
            username=plugin_conf["username"],
            password=plugin_conf["password"],
            project_name=project_name,
            project_domain_id=project_domainid,
            user_domain_id=user_domainid,
            region_name=region_name,
            ssl_verify=ssl_verify,
            http_timeout=http_timeout,
            request_batch_size=request_batch_size,
            list_servers_search_opts=nova_list_servers_search_opts,
        )
        OPENSTACK_CLIENT["nova"] = novametrics

        cindermetrics = CinderMetrics(
            auth_url=plugin_conf["authurl"],
            username=plugin_conf["username"],
            password=plugin_conf["password"],
            project_name=project_name,
            project_domain_id=project_domainid,
            user_domain_id=user_domainid,
            region_name=region_name,
            ssl_verify=ssl_verify,
            http_timeout=http_timeout,
        )
        OPENSTACK_CLIENT["cinder"] = cindermetrics

        neutronmetrics = NeutronMetrics(
            plugin_conf["authurl"],
            plugin_conf["username"],
            plugin_conf["password"],
            project_name,
            project_domainid,
            user_domainid,
            region_name,
            ssl_verify,
            http_timeout
        )
        OPENSTACK_CLIENT["neutron"] = neutronmetrics
        OPENSTACK_CLIENT["custdims"] = custom_dimensions

    except Exception as e:
        collectd.error("Failed to authenticate Openstack client due to {0}".format(e))

    if testing:
        return plugin_conf, OPENSTACK_CLIENT

    collectd.register_read(read_callback, interval, data=OPENSTACK_CLIENT, name=project_name)


def read_callback(data):
    try:
        custom_dims = data["custdims"]
        to_dispatch = metrics_to_dispatch(data["nova"].collect_hypervisor_metrics, custom_dims, "hypervisor")

        if data["query_server_metrics"]:
            to_dispatch += server_metrics_to_dispatch(data)

        to_dispatch += metrics_to_dispatch(data["nova"].collect_limit_metrics, custom_dims, "limit")
        to_dispatch += metrics_to_dispatch(data["cinder"].collect_cinder_metrics, custom_dims, "block storage")
        to_dispatch += metrics_to_dispatch(data["neutron"].collect_neutron_metrics, custom_dims, "network")

        for metrics in to_dispatch:
            dispatch_values(*metrics)

    except Exception as e:
        collectd.error("Failed to dispatch Openstack metrics due to {0}".format(e))


def metrics_to_dispatch(collector, custom_dims, metric_type):
    to_dispatch = []
    try:
        for v in collector().values():
            metrics, dims, props = v
            for (metric, value) in metrics:
                to_dispatch.append((metric, value, dims, props, custom_dims))
    except Exception as e:
        collectd.error("Failed to fetch {0} metrics due to {1}".format(metric_type, e))
        del to_dispatch[:]
    return to_dispatch


def server_metrics_to_dispatch(data):
    to_dispatch = []
    try:
        for v in data['nova'].collect_server_metrics().values():
            metrics, dims, props = v
            for (metric, value) in metrics:
                if metric.split(".")[3] in COUNTER_METRICS:
                    to_dispatch.append((metric, value, dims, props, data["custdims"], "counter"))
                else:
                    to_dispatch.append((metric, value, dims, props, data["custdims"]))
    except Exception as e:
        collectd.error("Failed to fetch server metrics due to {0}".format(e))
        del to_dispatch[:]
    return to_dispatch


def prepare_dims(dims, custdims):
    if bool(custdims) is False:
        return dims

    for (key, val) in custdims.items():
        dims[key] = val

    return dims


def _formatDimsForSignalFx(dims):
    formatted = ",".join(["{0}={1}".format(d, dims[d]) for d in dims])
    return "[{0}]".format(formatted) if formatted != "" else ""


def dispatch_values(metric, value, dims, props, custdims, metric_type="gauge"):
    dims = prepare_dims(dims, custdims)
    val = collectd.Values(type=metric_type)
    val.type_instance = "{0}{1}".format(metric, _formatDimsForSignalFx(dims))
    val.plugin = "openstack"
    val.plugin_instance = _formatDimsForSignalFx(props)
    val.values = [float(value)]
    val.dispatch()


if __name__ == "__main__":
    # run standalone
    pass
else:
    collectd.register_config(config_callback)
