# -*- coding: utf-8 -*-
import argparse
import configparser
import functools
import http.server
import importlib.metadata
import io
import json
import logging
import pathlib
import re
import signal
import threading
import typing
import urllib.parse
import urllib.request

from . import (
    checks,
    driver,
    driver_bitbucket,
    driver_github,
    driver_sandbox,
    fetch_endpoint,
)

LOG_LEVELS: typing.Dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


SPLIT_COMMA_RE: typing.Final = re.compile(r"\s*,\s*")


DRIVERS: typing.Final[dict[str, typing.Type[driver.DriverBase]]] = {
    "github": driver_github.Driver,
    "bitbucket": driver_bitbucket.Driver,
    "sandbox": driver_sandbox.Driver,
}


class HTTPError(RuntimeError):
    def __init__(self, code: int, message: str):
        super().__init__(f"HTTP {code} {message}")
        self.message = message
        self.code = code


class MyServer(http.server.BaseHTTPRequestHandler):
    def __init__(
        self,
        *args: typing.Any,
        drivers: list[driver.DriverBase],
        **kwargs: typing.Any,
    ):
        self._drivers = drivers
        self._logger = logging.getLogger("gerrit_checks_mock_fetch_endpoint")
        http.server.BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def log_message(self, format: str, *args: typing.Any) -> None:  # pylint: disable=redefined-builtin
        self._logger.debug("msg: " + format, *args)

    def do_HEAD(self) -> None:  # pylint: disable=invalid-name
        self.send_error(500, "Unsupported")

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        self.send_error(500, "Unsupported")

    def do_POST(self) -> None:  # pylint: disable=invalid-name
        try:
            url = urllib.parse.urlparse(self.path)
            if url.path == "/fetch":
                if self.headers["Accept"] != "application/json":
                    raise HTTPError(500, "Invalid accept header")
                if self.headers["Content-Type"] != "application/json":
                    raise HTTPError(500, "Invalid content-type")
                if "Content-Length" not in self.headers:
                    raise HTTPError(500, "No content")

                request = typing.cast(
                    fetch_endpoint.FetchEndpoint,
                    json.loads(
                        self.rfile.read(int(self.headers["Content-Length"])).decode(
                            "utf8",
                        ),
                    ),
                )

                self._logger.debug("request %s", request)

                runs: list[checks.CheckRun] = []
                for _driver in self._drivers:
                    runs.extend(_driver.run(request))

                response: checks.FetchResponse = checks.FetchResponse(  # type: ignore  # until python-3.11
                    responseCode=checks.ResponseCode.OK,
                    runs=runs,
                )

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=UTF-8")
                self.end_headers()
                self.send_response(200)
                response_wrapper = io.TextIOWrapper(self.wfile, write_through=True)

                #
                # Avoid double close
                #
                setattr(response_wrapper, "close", lambda: None)

                json.dump(response, response_wrapper)

                self._logger.debug("response %s", response)
            else:
                raise HTTPError(403, "Not found")

        except HTTPError as e:  # pylint: disable=invalid-name
            self._logger.error("Exception", exc_info=True)
            self.send_error(e.code, e.message)
        except Exception:  # pylint: disable=broad-except
            self._logger.error("Exception", exc_info=True)
            self.send_error(500, "Internal error")


def _setup_argparser(
    distribution: importlib.metadata.Distribution,
) -> argparse.ArgumentParser:

    name = getattr(
        distribution,
        "name",
        "gerrit_checks_mock_fetch_endpoint",
    )  # TODO: remove python-3.10  # pylint: disable=fixme

    parser = argparse.ArgumentParser(
        prog=name,
        description="Gerrit checks-mock plugin fetch endpoint",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{name}-{distribution.version}",
    )
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        choices=LOG_LEVELS.keys(),
        help=f"Log level {', '.join(LOG_LEVELS.keys())}",
    )
    parser.add_argument(
        "--log-file",
        metavar="FILE",
        help="Log file to use, default is stdout",
    )
    parser.add_argument(
        "--bind-address",
        metavar="ADDR",
        help="Bind address",
    )
    parser.add_argument(
        "--bind-port",
        metavar="PORT",
        type=int,
        help="Bind port",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        action="append",
        required=True,
        help="Configuration file, may be specified multiple times",
    )

    return parser


def _setup_log(
    args: argparse.Namespace,
    config: configparser.SectionProxy,
) -> None:
    handler = logging.StreamHandler()
    log_file = args.log_file or config.get("log_file")
    if log_file:
        handler.setStream(
            open(  # pylint: disable=consider-using-with
                log_file,
                "a",
                encoding="utf-8",
            ),
        )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            config.get(
                "logformat",
                fallback="%(asctime)s - %(levelname)-8s %(name)-15s %(message)s",
            ),
        ),
    )
    logging.getLogger(None).addHandler(handler)

    logger = logging.getLogger("gerrit_checks_mock_fetch_endpoint")
    logger.setLevel(LOG_LEVELS.get(args.log_level or config.get("log_level"), logging.INFO))


def main() -> None:
    try:
        distribution = importlib.metadata.distribution(
            "gerrit_checks_mock_fetch_endpoint",
        )
    except importlib.metadata.PackageNotFoundError:
        distribution = importlib.metadata.PathDistribution(path=pathlib.Path())

    args = _setup_argparser(distribution).parse_args()
    config = configparser.ConfigParser()
    for config_file in args.config:
        config.read(config_file)

    _setup_log(args, config["main"])
    logger = logging.getLogger("gerrit_checks_mock_fetch_endpoint")

    logger.info("Startup, version=%s", distribution.version)
    logger.debug("Args: %r", args)
    logger.debug("Config: %r", dict(((x, dict(y)) for x, y in config.items())))

    driver_names = config["main"].get("drivers")
    if not driver_names:
        raise RuntimeError("Please specify 'drivers' in configuration")

    drivers: list[driver.DriverBase] = []
    for driver_name in SPLIT_COMMA_RE.split(driver_names.strip()):
        driver_class: typing.Optional[typing.Type[driver.DriverBase]] = DRIVERS.get(
            driver_name,
        )
        if not driver_class:
            raise RuntimeError(f"Unsupported driver '{driver_name}'")
        drivers.append(driver_class(name=driver_name, config=config[driver_name]))

    server = http.server.HTTPServer(
        (
            args.bind_address or config["main"].get("bind_address", ""),
            args.bind_port or config["main"].getint("bind_port", 8080),
        ),
        functools.partial(
            MyServer,
            drivers=drivers,
        ),
    )

    def shutdown() -> None:
        threading.Thread(target=server.shutdown).start()

    signal.signal(
        signal.SIGTERM,
        lambda x, y: shutdown(),
    )
    signal.signal(
        signal.SIGINT,
        lambda x, y: shutdown(),
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    server.server_close()


if __name__ == "__main__":
    main()
