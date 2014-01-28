import os
import sys
from setuptools import setup, find_packages

LONG_DESCRIPTION = """
Django design patterns and REST API for field data collection.
"""


def parse_markdown_readme():
    """
    Convert README.md to RST via pandoc, and load into memory
    (fallback to LONG_DESCRIPTION on failure)
    """
    # Attempt to run pandoc on markdown file
    import subprocess
    try:
        subprocess.call(
            ['pandoc', '-t', 'rst', '-o', 'README.rst', 'README.md']
        )
    except OSError:
        return LONG_DESCRIPTION

    # Attempt to load output
    try:
        readme = open(os.path.join(
            os.path.dirname(__file__),
            'README.rst'
        ))
    except IOError:
        return LONG_DESCRIPTION
    return readme.read()


def create_wq_namespace():
    """
    Generate the wq namespace package
    (not checked in, as it technically is the parent of this folder)
    """
    if os.path.isdir("wq"):
        return
    os.makedirs("wq")
    init = open(os.path.join("wq", "__init__.py"), 'w')
    init.write("__import__('pkg_resources').declare_namespace(__name__)")
    init.close()


def create_wqdb_namespace():
    """
    Since tests aren't picking up package_dir, populate wq.db namespace with
    symlinks back to top level directories.
    """
    if os.path.isdir("wq/db"):
        return
    os.makedirs("wq/db")
    for folder in ("rest", "contrib", "patterns"):
        os.symlink("../../" + folder, "wq/db/" + folder)
    init = open(os.path.join("wq/db", "__init__.py"), 'w')
    init.write("")
    init.close()


def find_wq_packages(submodule):
    """
    Add submodule prefix to found packages, since the packages within each wq
    submodule exist at the top level of their respective repositories.
    """
    packages = ['wq', submodule]
    package_dir = {submodule: '.'}
    for package in find_packages():
        if package == 'wq':
            continue
        full_name = submodule + "." + package
        packages.append(full_name)
        package_dir[full_name] = package.replace('.', os.sep)

    return packages, package_dir


create_wq_namespace()
packages, package_dir = find_wq_packages('wq.db')

if len(sys.argv) > 1 and sys.argv[1] == "test":
    create_wqdb_namespace()

setup(
    name='wq.db',
    version='0.5.0-dev',
    author='S. Andrew Sheppard',
    author_email='andrew@wq.io',
    url='http://wq.io/wq.db',
    license='MIT',
    packages=packages,
    package_dir=package_dir,
    namespace_packages=['wq'],
    description=LONG_DESCRIPTION.strip(),
    long_description=parse_markdown_readme(),
    install_requires=[
        'Django>=1.5',
        'djangorestframework>=2.3.12',
        'south',
        'pystache',
        'python-social-auth',
        'swapper',
    ],
    classifiers=[
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
    test_suite='tests.runtests.main',
    tests_require=[
        'psycopg2',
        'celery',
        'wq.io>=0.4.1',
        'redis',
        'Pillow',
        'python-dateutil',
    ],
)
