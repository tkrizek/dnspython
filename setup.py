#!/usr/bin/env python
#
# Copyright (C) 2003-2007, 2009-2011 Nominum, Inc.
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
from distutils.core import setup
from Cython.Build import cythonize

srcs = [
    "dns/__init__.py",
    "dns/_compat.py",
    "dns/dnssec.py",
    "dns/e164.py",
    "dns/edns.py",
    "dns/entropy.py",
    "dns/exception.py",
    "dns/flags.py",
    "dns/grange.py",
    "dns/hash.py",
    "dns/inet.py",
    "dns/ipv4.py",
    "dns/ipv6.py",
    "dns/message.py",
    "dns/name.py",
    "dns/namedict.py",
    "dns/node.py",
    "dns/opcode.py",
    "dns/query.py",
    "dns/rcode.py",
    "dns/rdata.py",
    "dns/rdataclass.py",
    "dns/rdataset.py",
    "dns/rdatatype.py",
    "dns/rdtypes/ANY/AFSDB.py",
    "dns/rdtypes/ANY/AVC.py",
    "dns/rdtypes/ANY/CAA.py",
    "dns/rdtypes/ANY/CDNSKEY.py",
    "dns/rdtypes/ANY/CDS.py",
    "dns/rdtypes/ANY/CERT.py",
    "dns/rdtypes/ANY/CNAME.py",
    "dns/rdtypes/ANY/CSYNC.py",
    "dns/rdtypes/ANY/DLV.py",
    "dns/rdtypes/ANY/DNAME.py",
    "dns/rdtypes/ANY/DNSKEY.py",
    "dns/rdtypes/ANY/DS.py",
    "dns/rdtypes/ANY/EUI48.py",
    "dns/rdtypes/ANY/EUI64.py",
    "dns/rdtypes/ANY/GPOS.py",
    "dns/rdtypes/ANY/HINFO.py",
    "dns/rdtypes/ANY/HIP.py",
    "dns/rdtypes/ANY/ISDN.py",
    "dns/rdtypes/ANY/LOC.py",
    "dns/rdtypes/ANY/MX.py",
    "dns/rdtypes/ANY/NS.py",
    "dns/rdtypes/ANY/NSEC.py",
    "dns/rdtypes/ANY/NSEC3.py",
    "dns/rdtypes/ANY/NSEC3PARAM.py",
    "dns/rdtypes/ANY/OPENPGPKEY.py",
    "dns/rdtypes/ANY/PTR.py",
    "dns/rdtypes/ANY/RP.py",
    "dns/rdtypes/ANY/RRSIG.py",
    "dns/rdtypes/ANY/RT.py",
    "dns/rdtypes/ANY/SOA.py",
    "dns/rdtypes/ANY/SPF.py",
    "dns/rdtypes/ANY/SSHFP.py",
    "dns/rdtypes/ANY/TLSA.py",
    "dns/rdtypes/ANY/TXT.py",
    "dns/rdtypes/ANY/URI.py",
    "dns/rdtypes/ANY/X25.py",
    "dns/rdtypes/ANY/__init__.py",
    "dns/rdtypes/IN/A.py",
    "dns/rdtypes/IN/AAAA.py",
    "dns/rdtypes/IN/APL.py",
    "dns/rdtypes/IN/DHCID.py",
    "dns/rdtypes/IN/IPSECKEY.py",
    "dns/rdtypes/IN/KX.py",
    "dns/rdtypes/IN/NAPTR.py",
    "dns/rdtypes/IN/NSAP.py",
    "dns/rdtypes/IN/NSAP_PTR.py",
    "dns/rdtypes/IN/PX.py",
    "dns/rdtypes/IN/SRV.py",
    "dns/rdtypes/IN/WKS.py",
    "dns/rdtypes/IN/__init__.py",
    "dns/rdtypes/__init__.py",
    "dns/rdtypes/dnskeybase.py",
    "dns/rdtypes/dsbase.py",
    "dns/rdtypes/euibase.py",
    "dns/rdtypes/mxbase.py",
    "dns/rdtypes/nsbase.py",
    "dns/rdtypes/txtbase.py",
    "dns/renderer.py",
    "dns/resolver.py",
    "dns/reversename.py",
    "dns/rrset.py",
    "dns/set.py",
    "dns/tokenizer.py",
    "dns/tsig.py",
    "dns/tsigkeyring.py",
    "dns/ttl.py",
    "dns/update.py",
    "dns/version.py",
    "dns/wiredata.py",
    "dns/zone.py"]

cythonized = []
for src in srcs:
    cythonized += cythonize(src)

version = '1.16.0'

kwargs = {
    'name' : 'dnspython',
    'version' : version,
    'description' : 'DNS toolkit',
    'long_description' : \
    """dnspython is a DNS toolkit for Python. It supports almost all
record types. It can be used for queries, zone transfers, and dynamic
updates.  It supports TSIG authenticated messages and EDNS0.

dnspython provides both high and low level access to DNS. The high
level classes perform queries for data of a given name, type, and
class, and return an answer set.  The low level classes allow
direct manipulation of DNS zones, messages, names, and records.""",
    'author' : 'Bob Halley',
    'author_email' : 'halley@dnspython.org',
    'license' : 'BSD-like',
    'url' : 'http://www.dnspython.org',
    'packages' : ['dns', 'dns.rdtypes', 'dns.rdtypes.IN', 'dns.rdtypes.ANY'],
    'download_url' : \
    'http://www.dnspython.org/kits/%s/dnspython-%s.tar.gz' % (version, version),
    'classifiers' : [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: Freeware",
        "Operating System :: Microsoft :: Windows :: Windows 95/98/2000",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Internet :: Name Service (DNS)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        ],
    'test_suite': 'tests',
    'provides': ['dns'],
    'extras_require': {
        'IDNA': ['idna>=2.1'],
        'DNSSEC': ['pycrypto>=2.6.1', 'ecdsa>=0.13'],
        },
    'ext_modules': cythonized,
    }

setup(**kwargs)
