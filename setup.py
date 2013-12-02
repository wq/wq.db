from os.path import join, dirname
from setuptools import setup, find_packages

LONG_DESCRIPION = """
Django design patterns and REST API for field data collection.
"""

def long_description():
    """Return long description from README.rst if it's present
    because it doesn't get installed."""
    try:
        return open(join(dirname(__file__), 'README.rst')).read()
    except IOError:
        return LONG_DESCRIPTION

setup(
    name = 'wq.db',
    version = '0.4.0-dev',
    author='S. Andrew Sheppard',
    author_email='andrew@wq.io',
    url='http://wq.io/wq.db',
    license='MIT',
    packages=find_packages(),
    namespace_packages=['wq'],
    description='Django design patterns and REST API for field data collection.',
    long_description=long_description(),
    install_requires=[
        'Django>=1.5',
        'djangorestframework>=2.3.0',
        'south',
        'pystache',
        'django-social-auth'
    ],
    classifiers = [
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Database :: Database Engines/Servers',
    ],
)
