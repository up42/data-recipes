## Configuration for the Makefile.
SRC := $(shell pwd)
NGINX_HOST_PORT := 9898
## nginx configuration file.
NGINX_CONF := $(SRC)/nginx/nginx.conf
## Order logs.
ORDER_LOG := $(SRC)/log/up42_order_log.jsonl
## Options for running nginx locally. Replace the virtual host.
DOCKER_RUN_OPTIONS := -p $(NGINX_HOST_PORT):80 \
--mount type=bind,src=$(NGINX_CONF),dst=/etc/nginx/nginx.conf \
--mount type=bind,src=$(ORDER_LOG),dst=/var/log/nginx/up42_order_log.jsonl \
-d
