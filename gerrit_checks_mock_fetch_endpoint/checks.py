# -*- coding: utf-8 -*-
# flake8: noqa
# mypy: ignore-errors
# pylint: disable=unused-import, invalid-name, unused-argument, too-few-public-methods

from enum import Enum
from typing import Callable, List, Optional, TypedDict, Union

##### BEGIN OF LSP SPECS


class ChecksPluginApi:
    def register(
        self,
        provider: "ChecksProvider",
        config: Optional["ChecksApiConfig"] = None,
    ) -> None:
        pass

    def announceUpdate(self) -> None:
        pass

    def updateResult(self, run: "CheckRun", result: "CheckResult") -> None:
        pass


class ChecksApiConfig(TypedDict):
    fetchPollingIntervalSeconds: float


class ChangeData(TypedDict):
    changeNumber: float
    patchsetNumber: float
    patchsetSha: str
    repo: str
    commitMessage: Optional[str]
    changeInfo: "ChangeInfo"


class ChecksProvider:
    def fetch(self, change: ChangeData) -> "Promise[FetchResponse]":
        pass


class FetchResponse(TypedDict):
    responseCode: "ResponseCode"
    errorMessage: Optional[str]
    loginCallback: Optional[Callable[[], None]]
    actions: Optional[List["Action"]]
    summaryMessage: Optional[str]
    links: Optional[List["Link"]]
    runs: Optional[List["CheckRun"]]


class ResponseCode(str, Enum):
    OK = "OK"
    ERROR = "ERROR"
    NOT_LOGGED_IN = "NOT_LOGGED_IN"


class CheckRun(TypedDict):
    change: Optional[float]
    patchset: Optional[float]
    attempt: Optional[float]
    externalId: Optional[str]
    checkName: str
    checkDescription: Optional[str]
    checkLink: Optional[str]
    status: "RunStatus"
    statusDescription: Optional[str]
    statusLink: Optional[str]
    labelName: Optional[str]
    actions: Optional[List["Action"]]
    scheduledTimestamp: Optional["Date"]
    startedTimestamp: Optional["Date"]
    finishedTimestamp: Optional["Date"]
    results: Optional[List["CheckResult"]]


class Action(TypedDict):
    name: str
    tooltip: Optional[str]
    primary: Optional[bool]
    summary: Optional[bool]
    disabled: Optional[bool]
    callback: "ActionCallback"


ActionCallback = Callable[
    [float, float, Union[float, None], Union[str, None], Union[str, None], str],
    Union["Promise[ActionResult]", None],
]


class ActionResult(TypedDict):
    message: Optional[str]
    shouldReload: Optional[bool]
    errorMessage: Optional[str]


class RunStatus(str, Enum):
    RUNNABLE = "RUNNABLE"
    RUNNING = "RUNNING"
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"


class CheckResult(TypedDict):
    externalId: Optional[str]
    category: "Category"
    summary: str
    message: Optional[str]
    tags: Optional[List["Tag"]]
    links: Optional[List["Link"]]
    codePointers: Optional[List["CodePointer"]]
    actions: Optional[List[Action]]


class Category(str, Enum):
    SUCCESS = "SUCCESS"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Tag(TypedDict):
    name: str
    tooltip: Optional[str]
    color: Optional["TagColor"]


class TagColor(str, Enum):
    GRAY = "gray"
    YELLOW = "yellow"
    PINK = "pink"
    PURPLE = "purple"
    CYAN = "cyan"
    BROWN = "brown"


class Link(TypedDict):
    url: str
    tooltip: Optional[str]
    primary: bool
    icon: "LinkIcon"


class CodePointer(TypedDict):
    path: str
    range: "CommentRange"


class LinkIcon(str, Enum):
    EXTERNAL = "external"
    IMAGE = "image"
    HISTORY = "history"
    DOWNLOAD = "download"
    DOWNLOAD_MOBILE = "download_mobile"
    HELP_PAGE = "help_page"
    REPORT_BUG = "report_bug"
    CODE = "code"
    FILE_PRESENT = "file_present"


##### END OF LSP SPECS
