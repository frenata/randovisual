#!/bin/sh

echo "Starting varnishd"
varnishd -F -a :8080 -f /etc/varnish/default.vcl &

echo "Starting tileserv"
/usr/bin/pg_tileserv --config /config/pg_tileserv.toml
