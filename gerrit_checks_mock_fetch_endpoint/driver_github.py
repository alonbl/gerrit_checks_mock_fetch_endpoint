# -*- coding: utf-8 -*-
# pylint: disable=duplicate-code
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

    GITHUB_RUN_STATUS: typing.Final = {
        "queued": StatusInfo(
            status=checks.RunStatus.SCHEDULED,
            tags=(checks.Tag(name="QUEUED", tooltip="Queued", color=checks.TagColor.GRAY),),
        ),
        "in_progress": StatusInfo(
            status=checks.RunStatus.RUNNING,
            tags=(),
        ),
        "completed": StatusInfo(status=checks.RunStatus.COMPLETED, tags=()),
        "requested": StatusInfo(
            status=checks.RunStatus.SCHEDULED,
            tags=(
                checks.Tag(
                    name="REQUESTED",
                    tooltip="Requested",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
        "waiting": StatusInfo(
            status=checks.RunStatus.SCHEDULED,
            tags=(
                checks.Tag(
                    name="WAITING",
                    tooltip="Waiting",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
    }

    GITHUB_RUN_CONCLUSION: typing.Final = {
        "action_required": ConclusionInfo(
            category=checks.Category.WARNING,
            tags=(
                checks.Tag(
                    name="ACTION",
                    tooltip="Action required",
                    color=checks.TagColor.PINK,
                ),
            ),
        ),
        "cancelled": ConclusionInfo(
            category=checks.Category.INFO,
            tags=(
                checks.Tag(
                    name="CANCELED",
                    tooltip="Canceled",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
        "failure": ConclusionInfo(category=checks.Category.ERROR, tags=()),
        "neutral": ConclusionInfo(
            category=checks.Category.INFO,
            tags=(
                checks.Tag(
                    name="NATURAL",
                    tooltip="Natural",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
        "success": ConclusionInfo(category=checks.Category.SUCCESS, tags=()),
        "skipped": ConclusionInfo(
            category=checks.Category.INFO,
            tags=(
                checks.Tag(
                    name="SKIPPED",
                    tooltip="Skipped",
                    color=checks.TagColor.GRAY,
                ),
            ),
        ),
        "stale": ConclusionInfo(
            category=checks.Category.WARNING,
            tags=(checks.Tag(name="STALE", tooltip="Stale", color=checks.TagColor.GRAY),),
        ),
        "timed_out": ConclusionInfo(
            category=checks.Category.ERROR,
            tags=(
                checks.Tag(
                    name="TIMED_OUT",
                    tooltip="Timed out",
                    color=checks.TagColor.BROWN,
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
        # as negotiation is not working with GitHub
        #
        self._headers = {
            "Accept": "application/json",
            "Authorization": f"token {config['token']}",
        }

    def run(
        self,
        request: fetch_endpoint.FetchEndpoint,
    ) -> list[checks.CheckRun]:
        workflow_runs = self._json_fetcher(
            url=f"{self._base_url}/{{repo}}/actions/runs?{{query}}".format(
                repo=self._project_format.format(
                    repo=request["project"],
                ),
                query=urllib.parse.urlencode(
                    {
                        "branch": (
                            f"{self._branch_prefix}{request['changeId'] % 100:02}/"
                            + f"{request['changeId']}/{request['revision']}"
                        ),
                    },
                ),
            ),
            headers=self._headers,
        )

        ret: list[checks.CheckRun] = []

        for workflow_run in workflow_runs["workflow_runs"] if workflow_runs else ():

            cstatus = self.GITHUB_RUN_STATUS.get(
                workflow_run["status"],
                StatusInfo(
                    status=checks.RunStatus.COMPLETED,
                    tags=(
                        checks.Tag(
                            name="UNKNOWN",
                            tooltip=f"Unknown status {workflow_run['status']}",
                            color=checks.TagColor.PURPLE,
                        ),
                    ),
                ),
            )

            conclusion = workflow_run["conclusion"]
            if conclusion is None:
                cconclusion = ConclusionInfo(
                    category=checks.Category.INFO,
                    tags=(),
                )
            else:
                cconclusion = self.GITHUB_RUN_CONCLUSION.get(
                    conclusion,
                    ConclusionInfo(
                        category=checks.Category.WARNING,
                        tags=(
                            checks.Tag(
                                name="UNKNOWN",
                                tooltip=f"Unknown conclusion {conclusion}",
                                color=checks.TagColor.PURPLE,
                            ),
                        ),
                    ),
                )

            ret.append(
                checks.CheckRun(  # type: ignore  # until python-3.11
                    attempt=workflow_run["run_attempt"],
                    checkName=f"cm:gh:{workflow_run['name']}",
                    status=cstatus["status"],
                    results=(
                        checks.CheckRun(
                            category=cconclusion["category"],
                            summary=f"Workflow {workflow_run['name']}",
                            message=(
                                f"status={workflow_run['status']}\n"
                                + f"conclusion={workflow_run['conclusion']}\n"
                                + f"Workflow {workflow_run['path']}"
                            ),
                            tags=cstatus["tags"] + cconclusion["tags"],
                            links=(
                                checks.Link(
                                    url=workflow_run["html_url"],
                                    tooltop="GitHub action page",
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
