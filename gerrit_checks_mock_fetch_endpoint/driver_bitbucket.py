# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
import base64
import configparser
import typing
import urllib.parse

from . import checks, driver, fetch_endpoint


class StatusInfo(typing.TypedDict):
    status: checks.RunStatus
    tags: typing.Union[tuple[()], tuple[checks.Tag]]


class ConclusionInfo(typing.TypedDict):
    category: checks.Category
    tags: typing.Union[tuple[()], tuple[checks.Tag]]


class Driver(driver.DriverBase):  # pylint: disable=too-few-public-methods

    BITBUCKET_PIPELINE_STATE: typing.Final = {
        "pipeline_state_pending": StatusInfo(
            status=checks.RunStatus.SCHEDULED,
            tags=(
                checks.Tag(
                    name="PENDING",
                    tooltip="Pendding",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
        "pipeline_state_in_progress": StatusInfo(
            status=checks.RunStatus.RUNNING,
            tags=(),
        ),
        "pipeline_state_in_progress_paused": StatusInfo(
            status=checks.RunStatus.RUNNING,
            tags=(),
        ),
        "pipeline_state_completed": StatusInfo(
            status=checks.RunStatus.COMPLETED,
            tags=(),
        ),
        "pipeline_state_completed_failed": StatusInfo(
            status=checks.RunStatus.COMPLETED,
            tags=(),
        ),
    }

    BITBUCKET_PIPELINE_RESULT: typing.Final = {
        "pipeline_state_pending_pending": ConclusionInfo(
            category=checks.Category.INFO,
            tags=(),
        ),
        "pipeline_state_in_progress_running": ConclusionInfo(
            category=checks.Category.INFO,
            tags=(),
        ),
        "pipeline_state_completed_successful": ConclusionInfo(
            category=checks.Category.SUCCESS,
            tags=(),
        ),
        "pipeline_state_completed_stopped": ConclusionInfo(
            category=checks.Category.INFO,
            tags=(
                checks.Tag(
                    name="STOPPED",
                    tooltip="Stopped",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
        "pipeline_state_completed_failed": ConclusionInfo(
            category=checks.Category.ERROR,
            tags=(),
        ),
        "pipeline_state_in_progress_paused": ConclusionInfo(
            category=checks.Category.WARNING,
            tags=(
                checks.Tag(
                    name="PAUSED",
                    tooltip="Paused",
                    color=checks.TagColor.PINK,
                ),
            ),
        ),
    }

    def __init__(self, name: str, config: configparser.SectionProxy):
        super().__init__(name, config)

        self._base_url = config["base_url"]
        self._branch_prefix = config.get("branch_prefix", "changes/")
        self._project_format = config.get("repo_format", "{repo}-ci")

        #
        # Must set authorization header explicitly
        # and not via the authorizers.
        # as negotiation is not working with BitBucket
        #
        self._headers = {
            "Accept": "application/json",
            "Authorization": "Basic "
            + base64.b64encode(
                f"{config['user']}:{config['password']}".encode(
                    "utf8",
                ),
            ).decode("utf8"),
        }

    def run(
        self,
        request: fetch_endpoint.FetchEndpoint,
    ) -> list[checks.CheckRun]:
        pipelines = self._json_fetcher(
            url=f"{self._base_url}/{{project}}/pipelines/?{{query}}".format(
                project=self._project_format.format(
                    repo=request["project"],
                ),
                query=urllib.parse.urlencode(
                    {
                        "target.branch": (
                            f"{self._branch_prefix}{request['changeId'] % 100:02}/"
                            + f"{request['changeId']}/{request['revision']}"
                        ),
                        "sort": "-created_on",
                        "pagelen": 100,
                    },
                ),
            ),
            headers=self._headers,
        )

        ret: list[checks.CheckRun] = []

        for pipeline in pipelines["values"] if pipelines else ():

            cstate = self.BITBUCKET_PIPELINE_STATE.get(
                pipeline["state"]["type"],
                StatusInfo(
                    status=checks.RunStatus.COMPLETED,
                    tags=(
                        checks.Tag(
                            name="UNKNOWN",
                            tooltip=f"Unknown state {pipeline['state']['type']}",
                            color=checks.TagColor.PURPLE,
                        ),
                    ),
                ),
            )

            result_o = pipeline["state"].get("result") or pipeline["state"].get("stage")
            result = result_o["type"]
            if result is None:
                cresult = ConclusionInfo(
                    category=checks.Category.INFO,
                    tags=(),
                )
            else:
                cresult = self.BITBUCKET_PIPELINE_RESULT.get(
                    result,
                    ConclusionInfo(
                        category=checks.Category.WARNING,
                        tags=(
                            checks.Tag(
                                name="UNKNOWN",
                                tooltip=f"Unknown conclusion {result}",
                                color=checks.TagColor.PURPLE,
                            ),
                        ),
                    ),
                )

            ret.append(
                checks.CheckRun(  # type: ignore  # until python-3.11
                    attempt=pipeline["run_number"],
                    checkName=f"cm:bb:{pipeline['type']}",
                    status=cstate["status"],
                    results=(
                        checks.CheckRun(
                            category=cresult["category"],
                            summary=f"Workflow {pipeline['type']}",
                            message=(f"state={pipeline['state']['name']}\n" + f"result={result_o['name']}"),
                            tags=cstate["tags"] + cresult["tags"],
                            links=(
                                checks.Link(
                                    url=(
                                        f"{pipeline['repository']['links']['html']['href']}/"
                                        + f"pipelines/results/{pipeline['build_number']}"
                                    ),
                                    tooltop="BitBucket pipeline page",
                                    primary=True,
                                    icon=checks.LinkIcon.EXTERNAL,
                                ),
                            ),
                        ),
                    ),
                ),
            )

        return ret


__all__ = [
    "Driver",
]
