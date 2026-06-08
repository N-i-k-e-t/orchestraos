"""Agent roster tests."""

from shared.roster import load_all_registries


class TestAgentRoster:
    def test_fifty_plus_capabilities(self) -> None:
        roster = load_all_registries()
        assert len(roster) >= 50

    def test_ten_domains_represented(self) -> None:
        roster = load_all_registries()
        domains = {e.domain for e in roster}
        expected = {
            "Observation",
            "Detection",
            "Reasoning",
            "Cost",
            "Context",
            "Tool",
            "Reliability",
            "Remediation",
            "Learning",
            "Dashboard",
        }
        assert expected.issubset(domains)

    def test_learning_agents_present(self) -> None:
        names = {e.name for e in load_all_registries()}
        assert "IncidentLearningAgent" in names
        assert "PatternMiningAgent" in names
        assert "PolicyOptimizationAgent" in names
        assert "GroundingAgent" in names
        assert "ConfidenceAgent" in names
