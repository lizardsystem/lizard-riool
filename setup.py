from setuptools import setup

version = '1.0.3.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django >= 1.4',  # Needed because of bulk_create
    'python-dateutil >= 1.5,< 2.0',  # Needed because of celery
    'celery',
    'django-celery',
    'django-kombu',
    'django-extensions',
    'django-nose',
    'lizard-map >= 4.0, < 5.0',
    'lizard-ui >= 4.0, < 5.0',
    'pkginfo',
    'networkx',
    'sufriblib',
    ],

tests_require = [
    ]

setup(name='lizard-riool',
      version=version,
      description="TODO",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='TODO',
      author_email='TODO@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['lizard_riool'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
        'console_scripts': [],
        'lizard_map.adapter_class': [
          'lizard_riool_sewerage_adapter = lizard_riool.layers:SewerageAdapter',
        ]
      },
)
