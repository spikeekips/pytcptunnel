##################################################
pytcptunnel
##################################################

The `pytcptunnel` is the TCP request forwarding server, in theory it can handle
the almost every TCP-based protocol like `HTTP`, `HTTPS`, even in `ssh`.

In the case of `HTTPS`, it acts like well-known SSL-tunneling software,
`STUNNEL`, but `pytcptunnel` can append the `X-Forwarded-For` in the last line of
header.


Feature
##################################################

 - tcp forwarding
 - suport `HTTPS`
 - in HTTP/HTTPS, support `X-Forwarded-For`


Install
##################################################

From Source
==================================================

Requirement
--------------------------------------------------

 - `Python` 2.6 or higher <http://python.org>
 - `pyOpenSSL` 0.12 or higher <http://pyopenssl.sourceforge.net/>
 - `Twisted Network Framework` 10.1 or higher <http://twistedmatrix.com>

just use ``pip`` ::

    sh $ pip install Twisted pyOpenSSL


`setup.py`
--------------------------------------------------

#. Download the latest version of `pytcptunnel` from https://github.com/spikeekips/pytcptunnel/downloads
#. Run the `setup.py`::

    sh $ tar xf pytcptunnel-vX.X.X.tar.gz
    sh $ cd pytcptunnel-vX.X.X
    sh $ python -V
    sh $ python setup.py install

Everything done.


Generate Priv & Cert Key For HTTPS
==================================================

If you have some trouble to generate ssl private and certificate key file, see
this page, http://www.akadia.com/services/ssh_test_certificate.html .


Deploy
##################################################

After installation finished, it's ready to deply the `python`. The deploy script
are located at ``/bin`` from the installation root path ::

You can run the deploy script like this, ::

    sh $ pytcptunnel.py --base=https:*:443 --target=www.microsoft.com:8000 -n --ssl-priv-file=./server.key --ssl-cert-file=./server.crt -n

The client send the HTTPS request to the port 443 of this host and the every
request to port 443 of this host will be forwarded to the `www.microsoft.com`,
port 8000.

This will launch the `pytcptunnel` in background, as daemon. You can set these
kind of options manually, ::

    sh $ pytcptunnel --help
    Usage: pytcptunnel.py [options]
    Options:
      -n, --nodaemon                  don't daemonize, don't use default umask of
                                      0077
          --syslog                    Log to syslog, not to file
          --euid                      Set only effective user-id rather than real
                                      user-id. (This option has no effect unless the
                                      server is running as root, in which case it
                                      means not to shed all privileges after binding
                                      ports, retaining the option to regain
                                      privileges in cases such as spawning
                                      processes. Use with caution.)
          --vv                        verbose
          --without-x-forwarded-for   don't append `X-Forwarded-For` in the header
          --without-host-translation  don't translate the original `Host` header
      -l, --logfile=                  log to a specified file, - for stdout
      -p, --profile=                  Run in profile mode, dumping results to
                                      specified file
          --profiler=                 Name of the profiler to use (profile,
                                      cprofile, hotshot). [default: hotshot]
          --prefix=                   use the given prefix when syslogging [default:
                                      twisted]
          --pidfile=                  Name of the pidfile [default: twistd.pid]
          --chroot=                   Chroot to a supplied directory before running
      -u, --uid=                      The uid to run as.
      -g, --gid=                      The gid to run as.
          --umask=                    The (octal) file creation mask to apply.
      -B, --base=                     base server `protocol:host:port`
      -T, --target=                   target server `host:port`
          --ssl-priv-file=            SSL private key file
          --ssl-cert-file=            SSL certificate file
          --timeout=                  client timeout [default: 20]
          --help-reactors             Display a list of possibly available reactor
                                      names.
          --version                   Print version information and exit.
          --spew                      Print an insanely verbose log of everything
                                      that happens. Useful when debugging freezes or
                                      locks in complex code.
      -b, --debug                     Run the application in the Python Debugger
                                      (implies nodaemon), sending SIGUSR2 will drop
                                      into debugger
          --reactor=
          --help                      Display this help and exit.


Examples
################################################################################

::
    sh $ pytcptunnel.py --base=http:127.0.0.1:80 --target=www.microsoft.com:8080
    sh $ pytcptunnel.py --base=tcp:127.0.0.1:80 --target=www.microsoft.com:8080

This will forward the `HTTP` request from '127.0.0.1:80' to
'www.microsoft.com:8080', but the difference between the protocol part, `http`
or `tcp` is that with `http` protocol it can understand the `HTTP` protocol, so
add additional headers, `HOST` and `X-Forwarded-For`. In depending on the target
server, without `http` protocol, the request could not properly handled.

::
    sh $ pytcptunnel.py \
        --base=http:127.0.0.1:443 \
        --target=<http server>:80 \
        --ssl-priv-file=./privkey.pem \
        --ssl-cert-file=./cacert.pem \
        -h -n

This will bind the port, 443 in 127.0.0.1 and forward all the `HTTPs` request to
<http server>:80. For use `HTTPS`, `ssl-priv-file`, `ssl-cert-file` options must
be given.


