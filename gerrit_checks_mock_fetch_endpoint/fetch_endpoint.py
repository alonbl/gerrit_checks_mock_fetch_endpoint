# -*- coding: utf-8 -*-
import typing


class FetchEndpoint(typing.TypedDict):
    accountId: int
    emailAddresses: list[str]
    project: str
    changeId: int
    revision: int
