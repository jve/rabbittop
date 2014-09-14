""" RabbitMQ API
"""

import httplib
import base64
import os
import json
import collections
import datetime

import logging

_log = logging.getLogger()

# Use urllib.extra_quote to deal with weird names

def overview(host, user, password, port):
    return dict(_create_http_client(host, user, password, port, 'overview'))

def status(host, user, password, port, node_name=None):
    """ Return the status of the rabbitmq node.
    """
    if node_name:
        return dict(_create_http_client(host, user, password, port, 'nodes/{0}?memory=true'.format(node_name)))

    return _create_http_client(host, user, password, port, 'nodes')


def list_exchanges(host, user, password, port, vhost=''):
    """  List all the exchanges in a given vhost
    """
    return_values = collections.defaultdict(dict)
    for exchange in _create_http_client(host, user, password, port, 'exchanges/{0}'.format(vhost)):
        return_values[exchange.pop('vhost')][exchange.pop('name')] = exchange
    return dict(return_values)


def list_queues(host, user, password, port, vhost='', name=''):
    """ List all the queues in a given vhost
    """
    return _create_http_client(host, user, password, port, 'queues/{0}/{1}'.format(vhost, name))


def _create_http_client(host, user, password, port, path, data=None, method='GET'):
    """ Create a http client that will talk to the RabbitMQ http API.
    """
    if data:
        data = json.dumps(data)

    conn = httplib.HTTPConnection(host, port=int(port))
    credentials = base64.encodestring('{0}:{1}'.format(user, password)).replace('\n', '')
    headers = {
        'Authorization': "Basic {0}".format(credentials),
        'Content-Type': 'application/json'
    }
    _log.debug(os.path.join('/api', path))
    conn.request(method, os.path.join('/api', path), data, headers)
    result = conn.getresponse()
    result = result.read()

    return json.loads(result) if result else None


class Rabbit(object):

    message_stat_keys = ['publish', 'confirm', 'return_unroutable', ]

    def __init__(self, management_node, user, password, port, vhost=None):
        _overview = overview(management_node, user, password, port)
        self._vhost = vhost or ''
        self.version = _overview['rabbitmq_version']
        self.cluster_name = _overview.get('cluster_name')
        self.erlang_version = _overview['erlang_version']
        self.messages = {
            'total': {
                'count': _overview['queue_totals']['messages'],
                'rate': _overview['queue_totals']['messages_details']['rate']
            },
            'ready': {
                'count': _overview['queue_totals']['messages_ready'],
                'rate': _overview['queue_totals']['messages_ready_details']['rate']
            },
            'unacknowledged': {
                'count': _overview['queue_totals']['messages_unacknowledged'],
                'rate': _overview['queue_totals']['messages_unacknowledged_details']['rate']
            },
        }
        self._objects = _overview['object_totals']
        self._stats = _overview['message_stats']

        self._nodes = []
        nodes = status(management_node, user, password, port, node_name=None)
        for node in nodes:
            self._nodes.append(Node(node))

        self._queues = []
        queues = list_queues(management_node, user, password, port, vhost=self._vhost)
        for queue in queues:
            self._queues.append(RabbitQueue(queue))

        self.active_queues = False

    @property
    def nodes(self):
        return self._nodes

    @property
    def queues(self):
        if self.active_queues:
            return [queue for queue in self._queues if queue.state != 'idle']
        return self._queues

    @property
    def objects(self):
        return self._objects

    @property
    def details(self):
        keys = {
            'publish_details': 'Publish',
            'acknowledgment_details': 'Ack',
            'confirm_details': 'Confirm',
        }
        details = {}
        for key in keys:
            details[keys[key]] = self._stats.get(key, {'rate': 'N/A'})['rate']
        return details

class Node(object):
    def __init__(self, node_data):
        self.name = node_data['name']
        self.type = node_data['type']
        self.running = node_data['running']

        self.pid = node_data['os_pid']
        self.fd = node_data['fd_used']
        self.fd_total = node_data['fd_total']
        self.sockets_used = node_data['sockets_used']
        self.sockets_total = node_data['sockets_total']
        self.mem_used = node_data['mem_used']
        self.mem_limit = node_data['mem_limit']
        self.mem_alarm = node_data['mem_alarm']
        self.disk_free_limit = node_data['disk_free_limit']
        self.disk_free = node_data['disk_free']
        self.disk_free_alarm = node_data['disk_free_alarm']
        self.proc_used = node_data['proc_used']
        self.proc_totoal = node_data['proc_total']
        self.uptime = datetime.timedelta(milliseconds=node_data['uptime'])


class RabbitQueue(object):
    def __init__(self, queue_data):
        self.name = queue_data.get('name')
        self.vhost = queue_data.get('vhost')
        self.state = queue_data.get('state')
        self.policy = ''
        self.exclusive = ''
        self.params = ''
        self.state = ''
        self.total = queue_data.get('messages')
        self.total_rate = queue_data.get('messages_details', {'rate': 'N/A'})['rate']
        self.ready = queue_data.get('messages_ready')
        self.ready_rate = queue_data.get('messages_ready_details', {'rate': 'N/A'})['rate']
        self.unacked = queue_data.get('messages_unacknowledged')
        self.unacked_rate = queue_data.get('messages_unacknowledged_details', {'rate': 'N/A'})['rate']
        self.messages = {
            'total': {
                'count': queue_data.get('messages'),
                'rate': queue_data.get('messages_details', {'rate': 'N/A'})['rate']
            },
            'ready': {
                'count': queue_data.get('messages_ready'),
                'rate': queue_data.get('messages_ready_details', {'rate': 'N/A'})['rate']
            },
            'unacknowledged': {
                'count': queue_data.get('messages_unacknowledged'),
                'rate': queue_data.get('messages_unacknowledged_details', {'rate': 'N/A'})['rate']
            },
        }