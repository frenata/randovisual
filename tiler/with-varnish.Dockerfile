FROM ubuntu:latest AS builder
RUN apt update && apt install -y wget unzip
RUN wget -O pg_tileserv.zip https://postgisftw.s3.amazonaws.com/pg_tileserv_latest_linux.zip
RUN unzip pg_tileserv.zip && mv pg_tileserv /usr/bin

FROM varnish:latest

COPY --from=builder /usr/bin/pg_tileserv /usr/bin
COPY pg_tileserv.toml /config/pg_tileserv.toml
COPY default.vcl /etc/varnish/
COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
