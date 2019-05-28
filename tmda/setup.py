# bootstrap if we need to
try:
    import setuptools  # noqa
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import find_packages, setup


classifiers = ['Development Status :: 4 - Beta',
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
               'Topic :: Internet :: Proxy Servers',
               ]

setup( author = 'Jason R. Mastaler, Kevin Goodsell, Paul Jimenez, Chris Caputo, and others'
     , author_email = 'ccaputo@alt.net'
     , classifiers = classifiers
     , description = ('The Tagged Message Delivery Agent (TMDA) is a set of '
                      'anti-spam measures, including white-listing, black-listing,'
                      'challenge-response, and tagged addresses')
     , entry_points = { 'console_scripts': ['tmda-ofmipd = TMDA.ofmipd:main',
                                            'tmda-inject = TMDA.inject:main',
                                            'tmda-address = TMDA.address:main',
                                            'tmda-check-address = TMDA.check_address:main',
                                            'tmda-filter = TMDA.filter:main',
                                            'tmda-keygen = TMDA.keygen:main',
                                            'tmda-pending = TMDA.pending:main',
                                            'tmda-rfilter = TMDA.rfilter:main',
                                            'tmda-sendmail = TMDA.sendmail:main',
                                            ] }
     , name = 'TMDAretro'
     , packages = find_packages()
     , package_data =  { 'TMDA': [ 'templates/*' ] }
     , py_modules = []
     , url = 'https://github.com/ccaputo/TMDAretro'
     , version = '1.1.13'
     , zip_safe = False
     , install_requires = ['pyOpenSSL>=0.14',
                           'python-pam>=1.8.2',
                           'python-cdb>=0.35'
                           ]
     , extras_require = { }
     , tests_require = ['virtualenv>=1.11',
                        'pytest',
                        ]
      )
