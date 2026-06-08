#!/usr/bin/env python3
"""Print the full OrchestraOS agent/capability roster."""

from __future__ import annotations

from shared.console import configure_stdout_utf8
from shared.roster import load_all_registries


def main() -> None:
    configure_stdout_utf8()
    roster = load_all_registries()
    agents = [e for e in roster if e.kind == "agent"]
    capabilities = [e for e in roster if e.kind == "capability-of"]

    print(
        f"OrchestraOS Agent Roster — {len(roster)} total "
        f"({len(agents)} agents, {len(capabilities)} capabilities)\n"
    )
    print(f"{'Name':<32} {'Domain':<14} {'Service':<12} {'Kind':<16} {'Tested':<8} Module")
    print("-" * 110)
    for entry in roster:
        tested = "yes" if entry.tested else "no"
        print(
            f"{entry.name:<32} {entry.domain:<14} {entry.service:<12} "
            f"{entry.kind:<16} {tested:<8} {entry.module}"
        )

    print(f"\nREAL agent classes: {len(agents)}")
    print(f"Total capabilities (50+ claim): {len(roster)}")
    domains = sorted({e.domain for e in roster})
    print(f"Domains covered ({len(domains)}): {', '.join(domains)}")


if __name__ == "__main__":
    main()
