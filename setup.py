import os
import sys
from setuptools import setup, find_packages

LONG_DESCRIPTION = """
Django design patterns and REST API for citizen science field data collection.
"""


def readme():
    # Attempt to load markdown file
    try:
        readme = open('README.md')
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
    for folder in ("rest", "contrib", "patterns", "default_settings.py"):
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
        if package.split('.')[0] in ('wq', 'tests'):
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
    use_scm_version=True,
    author='S. Andrew Sheppard',
    author_email='andrew@wq.io',
    url='https://wq.io/wq.db',
    license='MIT',
    packages=packages,
    package_dir=package_dir,
    namespace_packages=['wq'],
    entry_points={'wq': 'wq.db=wq.db'},
    description=LONG_DESCRIPTION.strip(),
    long_description=readme(),
    long_description_content_type="text/markdown",
    install_requires=[
        'Django>=1.11,<4.0',
        'djangorestframework>=3.8.0,<3.12',
        'django-mustache',
        'html-json-forms',
        'natural-keys>=1.6.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Database :: Database Engines/Servers',
    ],
    test_suite='tests',
    setup_requires=[
        'setuptools_scm',
    ],
    project_urls={
        'Homepage': 'https://wq.io/wq.db',
        'Documentation': 'https://wq.io/docs/',
        'Source': 'https://github.com/wq/wq.db',
        'Release Notes': 'https://github.com/wq/wq.db/releases',
        'Issues': 'https://github.com/wq/wq.db/issues',
        'CI': 'https://travis-ci.org/wq/wq.db',
    },
)
