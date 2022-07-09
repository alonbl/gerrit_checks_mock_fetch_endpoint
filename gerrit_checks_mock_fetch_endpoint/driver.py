# -*- coding: utf-8 -*-
import abc
import configparser
import json
import logging
import typing
import urllib.request

from . import checks, fetch_endpoint

T = typing.TypeVar("T")


def non_none(var: typing.Optional[T]) -> T:
    if var is None:
        raise RuntimeError("Unexpected None")
    return var


class DriverBase(abc.ABC):  # pylint: disable=too-few-public-methods

    _logger: logging.Logger
    _config: configparser.SectionProxy

    def __init__(self, name: str, config: configparser.SectionProxy):
        self._name = name
        self._config = config
        self._timeout = config.getfloat("timeout", 2)

        self._logger = logging.getLogger(f"gerrit_checks_mock_fetch_endpoint.{name}")

        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(
                debuglevel=1 if self._logger.isEnabledFor(logging.DEBUG) else 0,
            ),
        )

    def __repr__(self) -> str:
        return self._name

    def _json_fetcher(self, url: str, headers: dict[str, str]) -> typing.Optional[typing.Any]:
        try:
            self._logger.debug("fetch url=%s timeout=%s", url, self._timeout)
            with self._opener.open(
                urllib.request.Request(url, headers=headers),
                timeout=self._timeout,
            ) as fetcher:
                resp = typing.cast(typing.Any, json.load(fetcher))
                self._logger.debug("resp data=%s", resp)
                return resp
        except Exception as e:  # pylint: disable=broad-except, invalid-name
            self._logger.error("Cannot communicate with '%s': %s", self._name, e)
            self._logger.debug("Exception", exc_info=True)
            return None

    @abc.abstractmethod
    def run(
        self,
        request: fetch_endpoint.FetchEndpoint,
    ) -> list[checks.CheckRun]:
        pass


__all__ = [
    "non_none",
    "DriverBase",
]
