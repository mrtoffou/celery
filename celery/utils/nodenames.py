# -*- coding: utf-8 -*-
"""Worker name utilities."""
from __future__ import absolute_import, unicode_literals

import os
import socket

from functools import partial

from kombu.entity import Exchange, Queue

from .functional import memoize
from .text import simple_format

#: Exchange for worker direct queues.
WORKER_DIRECT_EXCHANGE = Exchange('C.dq2')

#: Format for worker direct queue names.
WORKER_DIRECT_QUEUE_FORMAT = '{hostname}.dq2'

#: Separator for worker node name and hostname.
NODENAME_SEP = '@'

NODENAME_DEFAULT = 'celery'

gethostname = memoize(1, Cache=dict)(socket.gethostname)

__all__ = [
    'worker_direct', 'gethostname', 'nodename',
    'anon_nodename', 'nodesplit', 'default_nodename',
    'node_format', 'host_format',
]


def worker_direct(hostname):
    """Return :class:`kombu.Queue` that's a direct route to
    a worker by hostname.

    Arguments:
        hostname (str, ~kombu.Queue): The fully qualified node name of
            a worker (e.g. ``w1@example.com``).  If passed a
            :class:`kombu.Queue` instance it will simply return
            that instead.
    """
    if isinstance(hostname, Queue):
        return hostname
    return Queue(
        WORKER_DIRECT_QUEUE_FORMAT.format(hostname=hostname),
        WORKER_DIRECT_EXCHANGE,
        hostname,
    )


def nodename(name, hostname):
    """Create node name from name/hostname pair."""
    return NODENAME_SEP.join((name, hostname))


def anon_nodename(hostname=None, prefix='gen'):
    return nodename(''.join([prefix, str(os.getpid())]),
                    hostname or gethostname())


def nodesplit(nodename):
    """Split node name into tuple of name/hostname."""
    parts = nodename.split(NODENAME_SEP, 1)
    if len(parts) == 1:
        return None, parts[0]
    return parts


def default_nodename(hostname):
    name, host = nodesplit(hostname or '')
    return nodename(name or NODENAME_DEFAULT, host or gethostname())


def node_format(s, nodename, **extra):
    name, host = nodesplit(nodename)
    return host_format(
        s, host, name or NODENAME_DEFAULT, p=nodename, **extra)


def _fmt_process_index(prefix='', default='0'):
    from .log import current_process_index
    index = current_process_index()
    return '{0}{1}'.format(prefix, index) if index else default
_fmt_process_index_with_prefix = partial(_fmt_process_index, '-', '')


def host_format(s, host=None, name=None, **extra):
    host = host or gethostname()
    hname, _, domain = host.partition('.')
    name = name or hname
    keys = dict({
        'h': host, 'n': name, 'd': domain,
        'i': _fmt_process_index, 'I': _fmt_process_index_with_prefix,
    }, **extra)
    return simple_format(s, keys)