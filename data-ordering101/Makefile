## Include the configuration.
include config.mk

DOCKER := docker
## The docker image to be used.
IMAGE := nginx:mainline-alpine
## Container ID
CONTAINER_ID = $(shell $(DOCKER) ps -q -f "publish=$(NGINX_HOST_PORT)")

run:
	$(DOCKER) run $(DOCKER_RUN_OPTIONS) $(IMAGE)

list:
	$(DOCKER) ps -f "publish=$(NGINX_HOST_PORT)"

test:
	$(DOCKER) container exec $(CONTAINER_ID) nginx -t

reload:
	$(DOCKER) kill -s HUP $(CONTAINER_ID)

clean:
	$(DOCKER) system prune -f

stop:
	$(DOCKER) container stop $(CONTAINER_ID)

logs:
	$(DOCKER) container logs $(CONTAINER_ID)

restart: stop run

.PHONY: run reload restart test list clean stop logs
