import json

from service import agents


class BadPlanner:
    def complete(self, system, user):
        return json.dumps({"action": "delete_cluster"})


def test_write_tool_is_rejected_and_budget_enforced():
    result = agents.run_incident("High latency", BadPlanner(), agents.ReadOnlyTools({}, {}), max_steps=2)
    assert result["status"] == "step_limit"
    assert result["trace"][0]["observation"]["error"] == "tool not allowed"
