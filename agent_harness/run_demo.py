"""CLI entry point for side-by-side demo."""

import os

from agent_harness.scenario_autogpt import run_autogpt_scenario
from shared.console import configure_stdout_utf8
from tests.conftest import FakeRedisStore


def main() -> None:
    configure_stdout_utf8()
    collector = os.getenv("COLLECTOR_URL")
    run_autogpt_scenario(collector_url=collector, store=FakeRedisStore())


if __name__ == "__main__":
    main()
