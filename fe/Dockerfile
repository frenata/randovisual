FROM nginx

COPY index.html /usr/share/nginx/html
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
