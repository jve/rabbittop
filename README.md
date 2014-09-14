rabbit top
==========

rabbittop is a RabbitMQ command line viewer similar to top and htop build to monitor RabbitMQ.

It has build-in color based alerts when 75% and 95% thresholds are exceeded.

The displayed data can currently be filtered by vhost, additional filtering options will be added in the future.
Basic scrolling capabilities have been added to go through the list of queues.

It requires the RabbitMQ management API to be enabled.
It has been tested with python 2.7 and 2.6 and RabbitMQ 3.3.5, previous versions should work as long as the rabbitmq admin API does not change.
It has no further external dependencies.

Command line options:
---------------------

```
usage: rabbittop [-h] [-v VHOST] [-u USER] [-pw PASSWORD] [-p PORT] host
positional arguments:
  host                  Rabbit host to monitor
optional arguments:
  -h,           --help              show this help message and exit
  -v VHOST,     --vhost VHOST       vhost to monitor   (default=all)
  -u USER,      --user USER         user               (default=guest)
  -pw PASSWORD, --password PASSWORD password           (default=guest)
  -p PORT,      --port PORT         Management ui port (port=15672)
```

![](https://github.com/jve/rabbit_top/blob/master/screenshots/rabbittop.png)