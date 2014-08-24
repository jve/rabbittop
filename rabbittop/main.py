import atexit
import argparse
import curses
import sys
import time

from rabbittop import _rabbitmq, terminal, utils

memory_treshold_warning = 75
memory_treshold_error = 95

disk_space_treshold_warning = 75
disk_space_treshold_error = 95

process_threshold_warning = 75
process_threshold_error = 95

socket_threshold_warning = 75
socket_threshold_error = 95

messages_ready_warning = 10
messages_ready_error = 15

messages_unack_warning = 10
messages_unack_error = 15

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='Rabbit host to monitor')
    parser.add_argument('-v', '--vhost', help='vhost to monitor', default=None)
    parser.add_argument('-u', '--user', help='user', default='guest')
    parser.add_argument('-pw', '--password', help='password', default='guest')
    parser.add_argument('-p', '--port', help='Management ui port', default=15672)

    args = parser.parse_args()
    sys.exit(run(args))


def run(args):
    term = terminal.Terminal()
    atexit.register(term.stop)
    while True:
        rabbit = _rabbitmq.Rabbit(args.host, args.user, args.password, args.port, vhost=args.vhost)
        term.refresh()
        term.addLine(
            'rabbitmq-%s - erlang-%s - %s - %s' % (
                rabbit.version,
                rabbit.erlang_version,
                rabbit.cluster_name,
                time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
            ),
            0, 0,
            color=term.colors['TITLE']
        )
        line_index = 0
        for node in rabbit.nodes:
            line_index += 1
            node_line = '%s - type: %s - pid: %s - uptime: %s --' % (node.name, node.type, node.pid, str(node.uptime))
            term.addLine(
                node_line,
                line_index, 0,
                term.colors['TITLE'])
            column_count = len(node_line) + 1
            line_index, column_count = _disk_free(term, node, line_index, column_count)
            line_index, column_count = _mem_free(term, node, line_index, column_count+1)
            line_index, column_count = _process_free(term, node, line_index, column_count+1)
            line_index, column_count = _socket_count(term, node, line_index, column_count+1)

        line_index += 1
        column_count = 0
        line_index, column_count = _msg_rate(term, rabbit, line_index, column_count)
        line_index += 1
        column_count = 0
        line_index, column_count = _delivery_details(term, rabbit, line_index, column_count)
        line_index += 1
        column_count = 0
        line_index, column_count = _object_details(term, rabbit, line_index, column_count)
        line_index += 1
        column_count = 0

        _queue_details(term, rabbit, line_index, column_count)
        term.addLine("[a]ctive queues only", term.get_size()[0] - 1, 0, term.colors['REVERSE'])

        char = term.getch()
        if char == curses.KEY_UP:
            term.up()
            _queue_details(term, rabbit, line_index, column_count)
        elif char == curses.KEY_DOWN:
            term.down()
            _queue_details(term, rabbit, line_index, column_count)
        elif char == ord('a'):
            rabbit.active_queues = True if not rabbit.active_queues else False
        #elif char == self.SPACE_KEY:
        #    self.markLine()
        elif char == ord('q'):
            term.stop()
            break


def _disk_free(term, node, line_index, column_count):
    title = ' Disk usage:'
    term.addLine(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.disk_free)
    term.addLine(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color(
                node.disk_free_limit,
                node.disk_free,
                disk_space_treshold_warning,
                disk_space_treshold_error
            )
        ]
    )
    column_count += len(data)
    return line_index, column_count + 1


def _mem_free(term, node, line_index, column_count):
    title = ' Mem usage:'
    term.addLine(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.mem_used)
    term.addLine(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color(
                node.mem_used,
                node.mem_limit,
                memory_treshold_warning,
                memory_treshold_error
            )
        ]
    )
    column_count += len(data)
    return line_index, column_count + 1


def _process_free(term, node, line_index, column_count):
    title = ' Process usage:'
    term.addLine(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.proc_used)
    term.addLine(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color(
                node.proc_used,
                node.proc_totoal,
                process_threshold_warning,
                process_threshold_error
            )
        ]
    )
    column_count += len(data)
    return line_index, column_count + 1


def _socket_count(term, node, line_index, column_count):
    title = ' Socket usage:'
    term.addLine(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.sockets_used)
    term.addLine(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color(
                node.sockets_used,
                node.sockets_total,
                socket_threshold_warning,
                socket_threshold_error
            )
        ]
    )
    column_count += len(data)
    return line_index, column_count + 1


def _msg_rate(term, rabbit, line_index, column_count):
    title = 'Message rates \t '
    term.addLine(
        title,
        line_index, column_count,
        term.colors['TITLE']
    )
    column_count += len(title) + 1

    for key, value in rabbit.messages.iteritems():
        term.addLine(
            '%s:' % (key,),
            line_index, column_count,
            term.colors['TITLE']
        )
        column_count += len(key) + 1
        data = ' %s - %s msg/s\t\t' % (value['count'], value['rate'])
        term.addLine(
            data,
            line_index,
            column_count,
            term.colors[
                _calculate_color_values(
                    value['count'],
                    socket_threshold_warning,
                    socket_threshold_error
                )
            ]
        )
        column_count += len(data) + 1

    return line_index, column_count + 1

def _calculate_color(low_value, max_value, threshold_warning, threshold_error):
    percent = (float(low_value) / float(max_value)) * 100
    if percent >= threshold_warning and percent <= threshold_error:
        return 'CRITICAL'
    elif percent >= threshold_error:
        return 'CRITICAL_LOG'
    return 'OK'


def _calculate_color_values(value, threshold_warning, threshold_error):
    if value >= threshold_warning and value <= threshold_error:
        return 'CRITICAL'
    elif value >= threshold_error:
        return 'CRITICAL_LOG'
    return 'OK'

def _queue_details(term, rabbit, line_index, column_count):
    #import pdb; pdb.set_trace()
    term.addLine("\t\t\toverview\t\t\t\tmessages\t\t\trates\t\t\t\t", line_index, 0, term.colors['REVERSE'])
    line_index += 1
    term.addLine("NAME\tVHOST\tEXCL\tPARAMS\tPOLICY\tSTATE\t\tREADY\tUNACK\tTOTAL\t\tINC\tDELIVER/GET\tACK\t", line_index, 0, term.colors['TITLE'])
    line_index += 1

    max_length = term.get_size()[0] - line_index - 1 # removing one more line for bottom line

    start = max(term.start_row - term.selected_row, 0)
    if term.selected_row == 0:
        term.selected_row = line_index

    for queue in rabbit.queues[start: min(max_length + start, len(rabbit.queues))]:
        color = 'NICE' if line_index != term.selected_row else 'CAREFUL_LOG'
        term.addLine("%s\t%s\t%s\t%s\t%s\t%s\t\t%s\t%s\t%s\t\t%s\t%s\t\t%s\t" % (
            queue.name, queue.vhost, queue.exclusive, queue.params, queue.policy, queue.state, queue.ready, queue.unacked,
            queue.total, queue.total_rate, queue.ready_rate, queue.unacked_rate),
            line_index, 0,
            term.colors[color]
        )
        line_index += 1

    return line_index, column_count

def _object_details(term, rabbit, line_index, column_count):
    line = 'Objects \t '
    for key, value in rabbit.objects.iteritems():
        line += '%s: %s \t ' % (key, value)
    term.addLine(line, line_index, column_count, term.colors['TITLE'])
    return line_index, column_count

def _delivery_details(term, rabbit, line_index, column_count):
    line = 'Stats \t\t '
    for key, value in rabbit.details.iteritems():
        line += '%s: %s \t ' % (key, value)
    term.addLine(line, line_index, column_count, term.colors['TITLE'])
    return line_index, column_count
