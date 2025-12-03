#!/bin/sh
sed -i "s|TILER_URL_PLACEHOLDER|${TILER_URL}|g" /usr/share/nginx/html/index.html
nginx -g 'daemon off;'
