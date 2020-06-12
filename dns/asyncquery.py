# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2003-2017 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""Talk to a DNS server."""

import socket
import struct
import time

import dns.asyncbackend
import dns.exception
import dns.inet
import dns.name
import dns.message
import dns.rcode
import dns.rdataclass
import dns.rdatatype

from dns.query import _addresses_equal, _compute_times, UnexpectedSource, \
    BadResponse, ssl


# for brevity
_lltuple = dns.asyncbackend.low_level_address_tuple


def _source_tuple(af, address, port):
    # Make a high level source tuple, or return None if address and port
    # are both None
    if address or port:
        if address is None:
            if af == socket.AF_INET:
                address = '0.0.0.0'
            elif af == socket.AF_INET6:
                address = '::'
            else:
                raise NotImplementedError(f'unknown address family {af}')
        return (address, port)
    else:
        return None


def _timeout(expiration, now=None):
    if expiration:
        if not now:
            now = time.time()
        return max(expiration - now, 0)
    else:
        return None


async def send_udp(sock, what, destination, expiration=None):
    """Send a DNS message to the specified UDP socket.

    *sock*, a ``dns.asyncbackend.DatagramSocket``.

    *what*, a ``bytes`` or ``dns.message.Message``, the message to send.

    *destination*, a destination tuple appropriate for the address family
    of the socket, specifying where to send the query.

    *expiration*, a ``float`` or ``None``, the absolute time at which
    a timeout exception should be raised.  If ``None``, no timeout will
    occur.

    Returns an ``(int, float)`` tuple of bytes sent and the sent time.
    """

    if isinstance(what, dns.message.Message):
        what = what.to_wire()
    sent_time = time.time()
    n = await sock.sendto(what, destination, _timeout(expiration, sent_time))
    return (n, sent_time)


async def receive_udp(sock, destination, expiration=None,
                      ignore_unexpected=False, one_rr_per_rrset=False,
                      keyring=None, request_mac=b'', ignore_trailing=False,
                      raise_on_truncation=False):
    """Read a DNS message from a UDP socket.

    *sock*, a ``dns.asyncbackend.DatagramSocket``.

    *destination*, a destination tuple appropriate for the address family
    of the socket, specifying where the associated query was sent.

    *expiration*, a ``float`` or ``None``, the absolute time at which
    a timeout exception should be raised.  If ``None``, no timeout will
    occur.

    *ignore_unexpected*, a ``bool``.  If ``True``, ignore responses from
    unexpected sources.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its own
    RRset.

    *keyring*, a ``dict``, the keyring to use for TSIG.

    *request_mac*, a ``bytes``, the MAC of the request (for TSIG).

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the received message.

    *raise_on_truncation*, a ``bool``.  If ``True``, raise an exception if
    the TC bit is set.

    Raises if the message is malformed, if network errors occur, of if
    there is a timeout.

    Returns a ``dns.message.Message`` object.
    """

    wire = b''
    while 1:
        (wire, from_address) = await sock.recvfrom(65535)
        if _addresses_equal(sock.family, from_address, destination) or \
           (dns.inet.is_multicast(destination[0]) and
            from_address[1:] == destination[1:]):
            break
        if not ignore_unexpected:
            raise UnexpectedSource('got a response from '
                                   '%s instead of %s' % (from_address,
                                                         destination))
    received_time = time.time()
    r = dns.message.from_wire(wire, keyring=keyring, request_mac=request_mac,
                              one_rr_per_rrset=one_rr_per_rrset,
                              ignore_trailing=ignore_trailing,
                              raise_on_truncation=raise_on_truncation)
    return (r, received_time)

async def udp(q, where, timeout=None, port=53, source=None, source_port=0,
              ignore_unexpected=False, one_rr_per_rrset=False,
              ignore_trailing=False, raise_on_truncation=False, sock=None,
              backend=None):
    """Return the response obtained after sending a query via UDP.

    *q*, a ``dns.message.Message``, the query to send

    *where*, a ``str`` containing an IPv4 or IPv6 address,  where
    to send the message.

    *timeout*, a ``float`` or ``None``, the number of seconds to wait before the
    query times out.  If ``None``, the default, wait forever.

    *port*, an ``int``, the port send the message to.  The default is 53.

    *source*, a ``str`` containing an IPv4 or IPv6 address, specifying
    the source address.  The default is the wildcard address.

    *source_port*, an ``int``, the port from which to send the message.
    The default is 0.

    *ignore_unexpected*, a ``bool``.  If ``True``, ignore responses from
    unexpected sources.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its own
    RRset.

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the received message.

    *raise_on_truncation*, a ``bool``.  If ``True``, raise an exception if
    the TC bit is set.

    *sock*, a ``dns.asyncbackend.DatagramSocket``, or ``None``,
    the socket to use for the query.  If ``None``, the default, a
    socket is created.  Note that if a socket is provided, the
    *source* and *source_port* are ignored.

    *backend*, a ``dns.asyncbackend.Backend``, or ``None``.  If ``None``,
    the default, then dnspython will use the default backend.

    Returns a ``dns.message.Message``.
    """
    if not backend:
        backend = dns.asyncbackend.get_default_backend()
    wire = q.to_wire()
    (begin_time, expiration) = _compute_times(timeout)
    s = None
    try:
        if sock:
            s = sock
        else:
            af = dns.inet.af_for_address(where)
            stuple = _source_tuple(af, source, source_port)
            s = await backend.make_socket(af, socket.SOCK_DGRAM, 0, stuple)
            destination = _lltuple(af, (where, port))
        await send_udp(s, wire, destination, expiration)
        (r, received_time) = await receive_udp(s, destination, expiration,
                                               ignore_unexpected,
                                               one_rr_per_rrset,
                                               q.keyring, q.mac,
                                               ignore_trailing,
                                               raise_on_truncation)
        r.time = received_time - begin_time
        if not q.is_response(r):
            raise BadResponse
        return r
    finally:
        if not sock and s:
            await s.close()

async def udp_with_fallback(q, where, timeout=None, port=53, source=None,
                            source_port=0, ignore_unexpected=False,
                            one_rr_per_rrset=False, ignore_trailing=False,
                            udp_sock=None, tcp_sock=None, backend=None):
    """Return the response to the query, trying UDP first and falling back
    to TCP if UDP results in a truncated response.

    *q*, a ``dns.message.Message``, the query to send

    *where*, a ``str`` containing an IPv4 or IPv6 address,  where
    to send the message.

    *timeout*, a ``float`` or ``None``, the number of seconds to wait before the
    query times out.  If ``None``, the default, wait forever.

    *port*, an ``int``, the port send the message to.  The default is 53.

    *source*, a ``str`` containing an IPv4 or IPv6 address, specifying
    the source address.  The default is the wildcard address.

    *source_port*, an ``int``, the port from which to send the message.
    The default is 0.

    *ignore_unexpected*, a ``bool``.  If ``True``, ignore responses from
    unexpected sources.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its own
    RRset.

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the received message.

    *udp_sock*, a ``dns.asyncbackend.DatagramSocket``, or ``None``,
    the socket to use for the UDP query.  If ``None``, the default, a
    socket is created.  Note that if a socket is provided the *source*
    and *source_port* are ignored for the UDP query.

    *tcp_sock*, a ``dns.asyncbackend.StreamSocket``, or ``None``, the
    socket to use for the TCP query.  If ``None``, the default, a
    socket is created.  Note that if a socket is provided *where*,
    *source* and *source_port* are ignored for the TCP query.

    *backend*, a ``dns.asyncbackend.Backend``, or ``None``.  If ``None``,
    the default, then dnspython will use the default backend.

    Returns a (``dns.message.Message``, tcp) tuple where tcp is ``True``
    if and only if TCP was used.
    """
    try:
        response = await udp(q, where, timeout, port, source, source_port,
                             ignore_unexpected, one_rr_per_rrset,
                             ignore_trailing, True, udp_sock, backend)
        return (response, False)
    except dns.message.Truncated:
        response = await tcp(q, where, timeout, port, source, source_port,
                             one_rr_per_rrset, ignore_trailing, tcp_sock,
                             backend)
        return (response, True)


async def send_tcp(sock, what, expiration=None):
    """Send a DNS message to the specified TCP socket.

    *sock*, a ``socket``.

    *what*, a ``bytes`` or ``dns.message.Message``, the message to send.

    *expiration*, a ``float`` or ``None``, the absolute time at which
    a timeout exception should be raised.  If ``None``, no timeout will
    occur.

    Returns an ``(int, float)`` tuple of bytes sent and the sent time.
    """

    if isinstance(what, dns.message.Message):
        what = what.to_wire()
    l = len(what)
    # copying the wire into tcpmsg is inefficient, but lets us
    # avoid writev() or doing a short write that would get pushed
    # onto the net
    tcpmsg = struct.pack("!H", l) + what
    sent_time = time.time()
    await sock.sendall(tcpmsg, expiration)
    return (len(tcpmsg), sent_time)


async def _read_exactly(sock, count, expiration):
    """Read the specified number of bytes from stream.  Keep trying until we
    either get the desired amount, or we hit EOF.
    """
    s = b''
    while count > 0:
        n = await sock.recv(count, _timeout(expiration))
        if n == b'':
            raise EOFError
        count = count - len(n)
        s = s + n
    return s


async def receive_tcp(sock, expiration=None, one_rr_per_rrset=False,
                      keyring=None, request_mac=b'', ignore_trailing=False):
    """Read a DNS message from a TCP socket.

    *sock*, a ``socket``.

    *expiration*, a ``float`` or ``None``, the absolute time at which
    a timeout exception should be raised.  If ``None``, no timeout will
    occur.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its own
    RRset.

    *keyring*, a ``dict``, the keyring to use for TSIG.

    *request_mac*, a ``bytes``, the MAC of the request (for TSIG).

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the received message.

    Raises if the message is malformed, if network errors occur, of if
    there is a timeout.

    Returns a ``dns.message.Message`` object.
    """

    ldata = await _read_exactly(sock, 2, expiration)
    (l,) = struct.unpack("!H", ldata)
    wire = await _read_exactly(sock, l, expiration)
    received_time = time.time()
    r = dns.message.from_wire(wire, keyring=keyring, request_mac=request_mac,
                              one_rr_per_rrset=one_rr_per_rrset,
                              ignore_trailing=ignore_trailing)
    return (r, received_time)


async def tcp(q, where, timeout=None, port=53, source=None, source_port=0,
              one_rr_per_rrset=False, ignore_trailing=False, sock=None,
              backend=None):
    """Return the response obtained after sending a query via TCP.

    *q*, a ``dns.message.Message``, the query to send

    *where*, a ``str`` containing an IPv4 or IPv6 address, where
    to send the message.

    *timeout*, a ``float`` or ``None``, the number of seconds to wait before the
    query times out.  If ``None``, the default, wait forever.

    *port*, an ``int``, the port send the message to.  The default is 53.

    *source*, a ``str`` containing an IPv4 or IPv6 address, specifying
    the source address.  The default is the wildcard address.

    *source_port*, an ``int``, the port from which to send the message.
    The default is 0.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its own
    RRset.

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the received message.

    *sock*, a ``dns.asyncbacket.StreamSocket``, or ``None``, the
    socket to use for the query.  If ``None``, the default, a socket
    is created.  Note that if a socket is provided
    *where*, *port*, *source* and *source_port* are ignored.

    *backend*, a ``dns.asyncbackend.Backend``, or ``None``.  If ``None``,
    the default, then dnspython will use the default backend.

    Returns a ``dns.message.Message``.
    """

    if not backend:
        backend = dns.asyncbackend.get_default_backend()
    wire = q.to_wire()
    (begin_time, expiration) = _compute_times(timeout)
    s = None
    try:
        if sock:
            # Verify that the socket is connected, as if it's not connected,
            # it's not writable, and the polling in send_tcp() will time out or
            # hang forever.
            await sock.getpeername()
            s = sock
        else:
            # These are simple (address, port) pairs, not
            # family-dependent tuples you pass to lowlevel socket
            # code.
            af = dns.inet.af_for_address(where)
            stuple = _source_tuple(af, source, source_port)
            dtuple = (where, port)
            s = await backend.make_socket(af, socket.SOCK_STREAM, 0, stuple,
                                          dtuple, timeout)
        await send_tcp(s, wire, expiration)
        (r, received_time) = await receive_tcp(s, expiration, one_rr_per_rrset,
                                               q.keyring, q.mac,
                                               ignore_trailing)
        r.time = received_time - begin_time
        if not q.is_response(r):
            raise BadResponse
        return r
    finally:
        if not sock and s:
            await s.close()

async def tls(q, where, timeout=None, port=853, source=None, source_port=0,
              one_rr_per_rrset=False, ignore_trailing=False, sock=None,
              backend=None, ssl_context=None, server_hostname=None):
    """Return the response obtained after sending a query via TLS.

    *q*, a ``dns.message.Message``, the query to send

    *where*, a ``str`` containing an IPv4 or IPv6 address,  where
    to send the message.

    *timeout*, a ``float`` or ``None``, the number of seconds to wait before the
    query times out.  If ``None``, the default, wait forever.

    *port*, an ``int``, the port send the message to.  The default is 853.

    *source*, a ``str`` containing an IPv4 or IPv6 address, specifying
    the source address.  The default is the wildcard address.

    *source_port*, an ``int``, the port from which to send the message.
    The default is 0.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its own
    RRset.

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the received message.

    *sock*, an ``asyncbackend.StreamSocket``, or ``None``, the socket
    to use for the query.  If ``None``, the default, a socket is
    created.  Note that if a socket is provided, it must be a
    connected SSL stream socket, and *where*, *port*,
    *source*, *source_port*, and *ssl_context* are ignored.

    *backend*, a ``dns.asyncbackend.Backend``, or ``None``.  If ``None``,
    the default, then dnspython will use the default backend.

    *ssl_context*, an ``ssl.SSLContext``, the context to use when establishing
    a TLS connection. If ``None``, the default, creates one with the default
    configuration.

    *server_hostname*, a ``str`` containing the server's hostname.  The
    default is ``None``, which means that no hostname is known, and if an
    SSL context is created, hostname checking will be disabled.

    Returns a ``dns.message.Message``.
    """
    if not backend:
        backend = dns.asyncbackend.get_default_backend()
    if not sock:
        if ssl_context is None:
            ssl_context = ssl.create_default_context()
            if server_hostname is None:
                ssl_context.check_hostname = False
        else:
            ssl_context = None
            server_hostname = None
        af = dns.inet.af_for_address(where)
        stuple = _source_tuple(af, source, source_port)
        dtuple = (where, port)
        s = await backend.make_socket(af, socket.SOCK_STREAM, 0, stuple,
                                      dtuple, timeout, ssl_context,
                                      server_hostname)
    else:
        s = sock
    try:
        #
        # If a socket was provided, there's no special TLS handling needed.
        #
        return await tcp(q, where, timeout, port, source, source_port,
                         one_rr_per_rrset, ignore_trailing, s, backend)
    finally:
        if not sock and s:
            await s.close()
