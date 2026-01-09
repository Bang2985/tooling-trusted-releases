# 3.1. Running the server

**Up**: `3.` [Developer guide](developer-guide)

**Prev**: `2.1.` [Signing artifacts](signing-artifacts)

**Next**: `3.2.` [Overview of the code](overview-of-the-code)

**Sections**:

* [Introduction](#introduction)
* [Get the source](#get-the-source)
* [Run the server in an OCI container](#run-the-server-in-an-oci-container)
* [Run the server directly](#run-the-server-directly)

## Introduction

To develop ATR locally, we manage dependencies using [uv](https://docs.astral.sh/uv/). To run ATR on ASF hardware, we run it in containers managed by Puppet, but since this guide is about development, we focus on using Compose and uv. ATR can be developed on Linux or macOS. Windows and other platforms are not supported.

## Get the source

[Fork the source code](https://github.com/apache/tooling-trusted-releases/fork) of [ATR on GitHub](https://github.com/apache/tooling-trusted-releases), and then [clone your fork locally](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

There are lots of files and directories in the root of the ATR Git repository. The most important thing to know is that `atr/` contains the source code. ATR is a Python application based on [ASFQuart](https://github.com/apache/infrastructure-asfquart), which is based on [Quart](https://github.com/pallets/quart). The Quart web framework is an asynchronous version of [Flask](https://github.com/pallets/flask), a very widely used synchronous web framework. In addition to Python, we use small amounts of JavaScript and TypeScript for the front end.

Once you have the source, there are two ways of running the server: [in an OCI container](#run-the-server-in-an-oci-container), or [directly](#run-the-server-directly). The following sections explain how to do this. The trade off is that running in an OCI container gives more isolation from the system, but is slower. Running directly is fast, and does not require you to configure your browser to trust the certificate, but requires more manual set up. Do not use both methods simultaneously, because they share the same state directory and will conflict.

## Run the server in an OCI container

The easiest way to run the ATR server with all dependencies included is using Docker Compose. This builds an OCI container based on the Alpine Linux distribution that includes external tools such as CycloneDX, syft, and Apache RAT, syft which are required for SBOM generation and license checking.

To run ATR in a container, you need an OCI compatible container runtime with Compose support such as Docker or Podman. Then, in the ATR root source directory, use your Compose tool to bring the container up. If using Docker, for example, run:

```shell
mkdir -p state
[LDAP_BIND_DN=dn LDAP_BIND_PASSWORD=pass] docker compose up --build
```

The first build will take several minutes as Compose downloads and compiles dependencies. Subsequent runs will be faster due to caching.

This setup mounts your local `atr/` directory into the container, so code changes are reflected immediately without rebuilding. The containerised server runs with `--reload` enabled, and automatically restarts when files change.

The container runs in test mode (`ALLOW_TESTS=1`), which enables mock authentication. Visit [`https://127.0.0.1:8080/`](https://127.0.0.1:8080/) to access the site. You will need to accept the self-signed certificate. Browser vendors update the methods to achieve this, so documenting this is a moving target, but there is some advice from [Simple Web Server](https://github.com/terreng/simple-web-server/blob/main/website/src/docs/https.md#using-a-dummy-certificate-for-testing-purposes) and [IBM](https://github.com/IBM/fhe-toolkit-linux/blob/master/GettingStarted.md#step-4-accessing-the-toolkit) which may be useful and covers Chrome, Firefox, and Safari.

To stop the server, press `Ctrl+C` or run your Compose tool equivalent of `compose down` in the same directory in another terminal session. Do not run ATR in a container if also running it directly.

If you use are using Docker, you can start a terminal session in a container using `docker compose exec atr bash`, and you can start a container and run a shell instead of ATR using `docker compose run -rm atr bash`.

## Run the server directly

### Install dependencies

To run ATR directly, on the local machine, after cloning the source, you will need to install the following dependencies:

* [cmark](https://github.com/commonmark/cmark) (optional; for rebuilding documentation)
* Any [POSIX](https://en.wikipedia.org/wiki/POSIX) compliant [make](https://frippery.org/make/)
* [mkcert](https://github.com/FiloSottile/mkcert)
* [Python 3.13](https://www.python.org/downloads/release/python-3138/)
* [uv](https://docs.astral.sh/uv/#installation)

You can install Python 3.13 through your package manager or through uv. Here is how to install these dependencies on [Alpine Linux](https://en.wikipedia.org/wiki/Alpine_Linux):

```shell
apk add cmark curl git make mkcert@testing
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
uv python install 3.13
```

For macOS these instructions become:

```shell
brew install cmark mkcert
curl -LsSf https://astral.sh/uv/install.sh | sh
rehash
uv python install 3.13
```

### Run the server

Then, to run the server:

```shell
cd tooling-trusted-releases/
mkdir state
make certs-local
make serve-local
```

The `certs-local` step runs `mkcert localhost.apache.org 127.0.0.1 ::1` to generate a locally trusted TLS certificate. To avoid potential DNS resolution issues such as [those alluded to in RFC 8252](https://datatracker.ietf.org/doc/html/rfc8252#section-8.3), we do not include `localhost`. If the certificate is not trusted, you may have to follow the [mkcert guide](https://github.com/FiloSottile/mkcert/blob/master/README.md) to resolve the issue.

ATR requires TLS even for development because login is performed through the actual ASF OAuth server. This way, the development behavior aligns closely with the production behavior. We try to minimize differences between development and production environments.

Do not run ATR directly if also running it in an OCI container.

### Load the site

ATR will then be served on various hosts, but we recommend using only `localhost.apache.org`. This requires adding an entry to your `/etc/hosts` and potentially restarting your DNS server. If you do this, the following link should work:

[`https://localhost.apache.org:8080/`](https://localhost.apache.org:8080/)

If you do not want to change your `/etc/hosts`, you can use `127.0.0.1`. The following link should work:

[`https://127.0.0.1:8080/`](https://127.0.0.1:8080/)

Pick one or the other, because logging into the site on one host does not log you in to the site on any other host.

It will take one or two minutes for the server to fetch committee and project information from the ASF website. Until the fetch is complete, no existing committees and projects will show.

Developers without LDAP credentials will be unable to perform `rsync` writes and certain tasks may also fail. To enable these actions to succeed, visit `/user/cache` and press the "Cache me!" button. This writes your session information to the ATR state directory, where it will be consulted instead of an LDAP lookup if it exists. The same page also allows you to clear your session cache data. When you clear your session cache data, the `atr/principal.py` module will still likely cache your authorization, so you need to restart the server to clear that. This session caching feature only works in debug mode, which is enabled when using `make serve-local`.
