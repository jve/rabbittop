"""
The MIT License (MIT)

Copyright (c) 2014 Jozef van Eenbergen

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

"""
import atexit
import argparse
import curses
import sys
import time

from rabbittop import _rabbitmq, terminal, utils

# Thresholds
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

    parsed_args = parser.parse_args()
    sys.exit(curses.wrapper(run, parsed_args))


def run(scrn, args):
    term = terminal.Terminal(scrn=scrn)
    atexit.register(term.stop)
    while True:
        rabbit = _rabbitmq.Rabbit(args.host, args.user, args.password, args.port, vhost=args.vhost)
        term.refresh()
        term.add_line(
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
            term.add_line(node_line, line_index, 0, term.colors['TITLE'])
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

        # todo: Add filtering possibilities
        #term.add_line("[a]ctive queues only", term.get_size()[0] - 1, 0, term.colors['REVERSE'])

        char = term.getch()
        if char == curses.KEY_UP:
            term.panels['queues'].scroll_up()
        elif char == curses.KEY_DOWN:
            term.panels['queues'].scroll_down()
        elif char == ord('a'):
            rabbit.active_queues = True if not rabbit.active_queues else False
        elif char == ord('q'):
            term.stop()
            break


def _disk_free(term, node, line_index, column_count):
    """ Display disk stats
    """
    title = ' Disk usage:'
    term.add_line(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.disk_free)
    term.add_line(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color_percent(
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
    """ Display memory stats
    """
    title = ' Mem usage:'
    term.add_line(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.mem_used)
    term.add_line(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color_percent(
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
    """ Display process stats
    """
    title = ' Process usage:'
    term.add_line(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.proc_used)
    term.add_line(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color_percent(
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
    """ Display socket stats
    """
    title = ' Socket usage:'
    term.add_line(
        title,
        line_index, column_count,
        term.colors['TITLE'])

    column_count += len(title) + 1

    data = utils.human_size(node.sockets_used)
    term.add_line(
        ' %s ' % data,
        line_index,
        column_count,
        term.colors[
            _calculate_color_percent(
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
    """ Display message stats
    """
    title = 'Message rates \t '
    term.add_line(
        title,
        line_index, column_count,
        term.colors['TITLE']
    )
    column_count += len(title) + 1

    for key, value in rabbit.messages.iteritems():
        term.add_line(
            '%s:' % (key,),
            line_index, column_count,
            term.colors['TITLE']
        )
        column_count += len(key) + 1
        data = ' %s - %s msg/s\t\t' % (value['count'], value['rate'])
        term.add_line(
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


def _calculate_color_percent(low_value, max_value, threshold_warning, threshold_error):
    """ Calculate the color for a given value and warning and threshold values according to a percentage
    """
    percent = (float(low_value) / float(max_value)) * 100
    if percent >= threshold_warning and percent <= threshold_error:
        return 'CRITICAL'
    elif percent >= threshold_error:
        return 'CRITICAL_LOG'
    return 'OK'


def _calculate_color_values(value, threshold_warning, threshold_error):
    """ Calculate the color for a given value and warning and threshold values according to a value
    """
    if value >= threshold_warning and value <= threshold_error:
        return 'CRITICAL'
    elif value >= threshold_error:
        return 'CRITICAL_LOG'
    return 'OK'


def _queue_details(term, rabbit, line_index, column_count):
    """ Display queue stats in a scrollable panel
    """
    queues = rabbit.queues
    height, width = term.get_size()
    panel_height = max(height - line_index, len(queues))

    panel = term.panels.get('queues') or term.create_panel('queues', panel_height - line_index - 2, width)

    term.add_line("\t\t\toverview\t\t\t\tmessages\t\t\trates\t\t\t\t", line_index, 0, term.colors['REVERSE'])
    line_index += 1
    term.add_line("NAME\tVHOST\tEXCL\tPARAMS\tPOLICY\tSTATE\t\tREADY\tUNACK\tTOTAL\t\tINC\tDELIVER/GET\tACK\t", line_index, 0, term.colors['TITLE'])
    line_index += 1

    _old_line_index = line_index
    line_index = 0

    if term.selected_row is None:
        term.selected_row = line_index

    for queue in queues:
        # todo: support highlighting of queues
        #color = 'NICE' if line_index != term.selected_row else 'CAREFUL_LOG'
        panel.add_line("%s\t%s\t%s\t%s\t%s\t%s\t\t%s\t%s\t%s\t\t%s\t%s\t\t%s\t" % (
            queue.name, queue.vhost, queue.exclusive, queue.params, queue.policy, queue.state, queue.ready, queue.unacked,
            queue.total, queue.total_rate, queue.ready_rate, queue.unacked_rate),
            line_index, 0,
            term.colors['NICE']
        )
        line_index += 1

    # first 2 arguments what to show of the panel
    # second 2 arguments where to show the panel on the screen
    # last 2 arguments until where to show it.
    panel.refresh(panel.ptopy, 0, _old_line_index, 0, height - _old_line_index - 2, width)
    panel.set_max(panel_height - (height - _old_line_index))
    return _old_line_index + line_index, column_count


def _object_details(term, rabbit, line_index, column_count):
    """ Display objects stats
    """
    line = 'Objects \t '
    for key, value in rabbit.objects.iteritems():
        line += '%s: %s \t ' % (key, value)
    term.add_line(line, line_index, column_count, term.colors['TITLE'])
    return line_index, column_count


def _delivery_details(term, rabbit, line_index, column_count):
    """ Display delivery stats
    """
    line = 'Stats \t\t '
    for key, value in rabbit.details.iteritems():
        line += '%s: %s \t ' % (key, value)
    term.add_line(line, line_index, column_count, term.colors['TITLE'])
    return line_index, column_count