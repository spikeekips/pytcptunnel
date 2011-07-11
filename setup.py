# -*- coding: utf-8 -*-

from distutils.core import setup

long_description = """
The `pytcptunnel` is the TCP request forwarding server, in theory it can handle
the almost every TCP-based protocol like `HTTP`, `HTTPS`, even in `ssh`.
"""


setup(
    name="pytcptunnel",
    version="0.1",
    description="TCP request forwarding server",
    long_description=long_description.replace("\n", " ").strip(),
    author="Spike^ekipS",
    author_email="spikeekips@gmail.com",
    url="https://github.com/spikeekips/pytcptunnel",
    download_url="https://github.com/spikeekips/pytcptunnel/downloads",
    platforms=["Any", ],
    license="GNU General Public License (GPL)",

    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
		"Programming Language :: Python :: 2.7",
		"Topic :: System :: Networking",
		"Topic :: Internet :: WWW/HTTP",
		"Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Security",
        "Topic :: System :: Systems Administration",
    ),

    data_files=(
        ("bin", ("src/pytcptunnel.py", ), ),
    ),

    install_requires=(
        "Twisted>=10.1.0",
        "pyOpenSSL>=0.12",
    ),

)
