FROM varnish

COPY default.vcl /etc/varnish/
COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
