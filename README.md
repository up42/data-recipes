# UP42 Data recipes

## Introduction

This repository contains code recipes to use and explore the
[UP42 data platform](https://docs.up42.com/data).

The concept of recipes relies on employing the most **expedient** way
to use and explore the UP42 data platform.

The concept of recipes borrows from cookbooks and the idea is to
provide developers with pragmatic how-tos. Similar to coooking we draw
from multiple _ingredients_, meaning technologies. They intend to be
as simple as possible while exploring the full range of possibilities,
offered by the UP42 data platform.

## Recipe list

 * **Data ordering 101**: how-to
    1. Search for data.
    2. Place an order to acquire the data selected in 1.
    3. Get notified via a webhook when the data ordered in 2 is
       delivered.
    4. Go to 1 for order more data.

## Data ordering 101

The code relative to this recipe is on the `data-ordering101` directory.

### Ingredients (Requirements)

To be able to run the **server side** version of the code you need:

 1. [docker](https://docs.docker.com/install/).
 2. [GNU make](https://www.gnu.org/software/make/).
 3. [Jupyter](https://juypter.org).
 4. [nginx](https://nginx.org/)
 5. [ngrok 2](ngrok.com) and an account to use it.
 6. [pipedream](https://pipedream.com) and an account to use it.
 7. [UP42 SDK](https://sdk.up42.com/)
 8. Minimal knowledge of Python.
 9. An [UP42](https://up42.com) account.

### Makefile

 * `run`: run nginx from a dockerhub image using port `9898`.
 * `list`: list the containers using port `9898`.
 * `test`: test the nginx configuration
     (do `nginx -t` on the running container).
 * `reload`: reload the nginx configuration.
 * `restart`: restart nginx.
 * `stop`: stop nginx.
 * `logs`: show the nginx logs.

### Pipedream snippets

The pipedream snippets are in the snippets directory. And the
filenames are self explanatory:

 * `pipedream_up42_webhook_order_status_handler.py`: incoming HTTP
   validation and order status filtering.

 * `pipedream_order_info_http_forwarder.py`: forward the webhook
   information to our local nginx instance. This is done via GET
   request where the order information is sent in a custom HTTP header.

### nginx configuration

The `nginx` directory contains:

 * `mnginx.conf`: server configuration.

### Jupyter notebook

In the `notebooks` directory there is a Python
[Jupyter](https://jupyter.org) notebook that makes use of the
[UP42 SDK](https://sdk.up42.com/) to setup the webhook, search and
order data.

 * `data_ordering101.ipynb`.

### Using this code

For a detailed description of the usage of this code please refer to
the UP42 blog post that elaborates on how to use it.

 * [Blog post on data ordering 101](https://up42.com/blog/tech/data-ordering101).

## License

MIT License

Copyright (c) 2022 UP42 GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
