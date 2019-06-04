# bootstrap if we need to
try:
    import setuptools  # noqa
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import find_packages, setup
from glob import glob
import os
from TMDA import Version


classifiers = [ 'Development Status :: 4 - Beta',
                'Environment :: Console',
                'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                'Intended Audience :: System Administrators',
                'Natural Language :: English',
                'Operating System :: MacOS :: MacOS X',
                'Operating System :: Microsoft :: Windows',
                'Operating System :: POSIX',
                'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: Implementation :: CPython',
                'Topic :: Communications :: Email :: Filters',
                'Topic :: Internet :: Proxy Servers' ]

setup(
    name = 'TMDAretro',
    description = ('The Tagged Message Delivery Agent (TMDA) is a set of '
                   'anti-spam measures, including white-listing, black-listing, '
                   'challenge-response, and tagged addresses.'),
    long_description_content_type = 'text/x-rst',
    long_description = \
"""
TMDA is an open source software application designed to significantly
reduce the amount of spam (Internet junk-mail) you receive.  TMDA
strives to be more effective, yet less time-consuming than traditional
spam filters.  TMDA can also be used as a general purpose local mail
delivery agent to filter, sort, deliver and dispose of incoming mail.

The technical countermeasures used by TMDA to thwart spam include:

* whitelists: accept mail from known, trusted senders.

* blacklists: refuse mail from undesired senders.

* challenge/response: allows unknown senders which aren't on the
  whitelist or blacklist the chance to confirm that their message is
  legitimate (non-spam).

* tagged addresses: special-purpose e-mail addresses such as
  time-dependent addresses, or addresses which only accept certain
  kinds of communication.  These increase the transparency of TMDA for
  unknown senders by allowing them to safely circumvent the
  challenge/response system.

This version/package results:

1. from the original TMDA 1.1.12 source code (apparently no longer maintained as of July 2007)

2. Git-imported and further maintained by Kevin Goodsell at https://github.com/KevinGoodsell/tmda-fork (apparently no longer maintained as of May 2011)

3. further maintained by Chris Caputo at https://github.com/ccaputo/TMDAretro (since May 2019)
""",
    version = Version.TMDA,
    author = 'Jason R. Mastaler, Kevin Goodsell, Paul Jimenez, Cedric Dufour, Chris Caputo, and others',
    author_email = 'ccaputo@alt.net',
    license = 'GPL-2',
    url = 'http://tmda.net',
    download_url = 'https://github.com/ccaputo/TMDAretro',
    classifiers = classifiers,
    py_modules = [],
    zip_safe = False,
    install_requires = [ 'pyOpenSSL>=0.14',
                         'python-pam>=1.8.2',
                         'python-cdb>=0.34' ],
    extras_require = { },
    tests_require = [ 'virtualenv>=1.11',
                      'pytest' ],
    packages = [ 'TMDA', 'TMDA.Queue' ],
    data_files = [ ('share/tmda/doc', [ 'CODENAMES', 'COPYING', 'CRYPTO', 'ChangeLog', 'NEWS', 'README', 'README.md', 'THANKS', 'UPGRADE' ]),
                   ('share/tmda/templates', [f for f in glob('templates/*') if os.path.isfile(f)]),
                   ('share/tmda/skeleton/dot-tmda', [f for f in glob('contrib/dot-tmda/*') if os.path.isfile(f)]),
                   ('share/tmda/skeleton/dot-tmda/filters', [f for f in glob('contrib/dot-tmda/filters/*') if os.path.isfile(f)]),
                   ('share/tmda/skeleton/dot-tmda/lists', [f for f in glob('contrib/dot-tmda/lists/*') if os.path.isfile(f)]) ],
    scripts = [ 'bin/tmda-address',
                'bin/tmda-check-address',
                'bin/tmda-filter',
                'bin/tmda-inject',
                'bin/tmda-keygen',
                'bin/tmda-ofmipd',
                'bin/tmda-pending',
                'bin/tmda-rfilter',
                'bin/tmda-sendmail' ]
)
