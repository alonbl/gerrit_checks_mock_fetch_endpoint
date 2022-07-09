# -*- coding: utf-8 -*-

from . import checks, driver, fetch_endpoint


class Driver(driver.DriverBase):  # pylint: disable=too-few-public-methods
    def run(
        self,
        request: fetch_endpoint.FetchEndpoint,
    ) -> list[checks.CheckRun]:
        return [
            checks.CheckRun(  # type: ignore  # until python-3.11
                checkName="cm:sb:Checks Mock - Check1",
                checkDescription="Description1",
                status=checks.RunStatus.COMPLETED,
                statusLink="https://www.google.com",
                results=(
                    checks.CheckRun(
                        category=checks.Category.ERROR,
                        summary="Summary1",
                        message="Message1",
                    ),
                    checks.CheckRun(
                        category=checks.Category.SUCCESS,
                        summary="Summary2",
                        message="Message2",
                        tags=(
                            checks.Tag(
                                name="Name1",
                                tooltip="Top1",
                                color=checks.TagColor.PINK,
                            ),
                        ),
                        links=(
                            checks.Link(
                                url="https://www.google.com",
                                tooltip="Tip1",
                                primary=True,
                                icon=checks.LinkIcon.DOWNLOAD,
                            ),
                        ),
                    ),
                ),
            ),
            checks.CheckRun(  # type: ignore  # until python-3.11
                checkName="cm:sb:Checks Mock - Check2",
                checkDescription="Description2",
                status=checks.RunStatus.COMPLETED,
                statusLink="https://www.google.com",
                results=(
                    checks.CheckRun(
                        category=checks.Category.ERROR,
                        summary="Summary1",
                        message="Message1",
                    ),
                    checks.CheckRun(
                        category=checks.Category.SUCCESS,
                        summary="Summary2",
                        message="Message2",
                        tags=(
                            checks.Tag(
                                name="Name1",
                                tooltip="Top1",
                                color=checks.TagColor.PINK,
                            ),
                        ),
                        links=(
                            checks.Link(
                                url="https://www.google.com",
                                tooltip="Tip1",
                                primary=True,
                                icon=checks.LinkIcon.DOWNLOAD,
                            ),
                        ),
                    ),
                ),
            ),
        ]


__all__ = [
    "Driver",
]
