#!/bin/bash
flake8 --max-line-length 120 openstack_metrics.py urllib_ssl_handler.py

if [ "$?" -ne 0 ]; then
	exit 1;
fi

py.test test_openstack.py
