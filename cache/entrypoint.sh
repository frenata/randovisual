#!/bin/sh
sed -i "s|TILER_URL_PLACEHOLDER|${VARNISH_BACKEND_HOST}|g" /etc/varnish/default.vcl
exec varnishd -F -a :80 -f /etc/varnish/default.vcl
