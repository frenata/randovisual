# Important documentation links:
# - general entry point: https://www.varnish-cache.org/docs/
# - VCL primer: https://varnish-cache.org/docs/2.1/tutorial/vcl.html
# - more VCL information: https://www.varnish-software.com/developers/tutorials/varnish-configuration-language-vcl/
# - logging: https://docs.varnish-software.com/tutorials/vsl-query/

vcl 4.1;

# https://github.com/varnish/toolbox/tree/master/vcls/hit-miss
include "hit-miss.vcl";

# import vmod_dynamic for better backend name resolution
import std;

# Before you configure anything, we just disable the backend to avoid
# any mistake, but you can delete that line and uncomment the following
# ones to define a proper backend to fetch content from
# backend default none;

backend default {
   .host = "localhost";
   .port = "7800";
}

# we may not have ipv6 in a container, so we'll only contact backend using ipv4
# acl ipv4_only { "0.0.0.0"/0; }

# create a director that can find backends on-the-fly
# sub vcl_init {
# 	new vdir = directors.round_robin();
# 	vdir.add_backend(default);
# }

# VCL allows you to implement a series of callback to dictate how to process
# each request. vcl_recv is the first one being called, right after Varnish
# receives some request headers. It's usually used to sanitize the request
sub vcl_recv {
  if (req.method == "OPTIONS") {
    return (synth(200, "OK"));
  }
}


sub vcl_deliver {
    set resp.http.Access-Control-Allow-Origin = "*";
    set resp.http.Access-Control-Allow-Headers = "Content-Type, Authorization";
}

sub vcl_synth {
       if (req.method == "OPTIONS") {
         set resp.http.Access-Control-Allow-Origin = "*";
         set resp.http.Access-Control-Allow-Methods = "GET, OPTIONS";
         set resp.http.Access-Control-Allow-Headers = "Content-Type, Authorization, Access-Control-Allow-Origin";
         set resp.http.Access-Control-Max-Age = "86400";
	 set resp.status = 200;
         return (deliver);
       }
}

# if no synthetic response was generated, the request will go the the backend.
# vcl_backend_response is your chance to sanitize the response and possibly to
# set a TTL
sub vcl_backend_response {
    if (bereq.url ~ "^/public.ride_routes/^") {
        set beresp.ttl = 30d;
    }
}

# https://github.com/varnish/toolbox/tree/master/vcls/verbose_builtin
include "verbose_builtin.vcl";
