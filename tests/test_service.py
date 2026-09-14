import json

from service import agents


class BadPlanner:
    def complete(self, system, user):
        return json.dumps({"action": "delete_cluster"})


def test_write_tool_is_rejected_and_budget_enforced():
    result = agents.run_incident("High latency", BadPlanner(), agents.ReadOnlyTools({}, {}), max_steps=2)
    assert result["status"] == "step_limit"
    assert result["trace"][0]["observation"]["error"] == "tool not allowed"


class SequencePlanner:
    def __init__(self, decisions):
        self.decisions = iter(decisions)

    def complete(self, system, user):
        return json.dumps(next(self.decisions))


def test_finish_requires_observed_evidence():
    tools = agents.ReadOnlyTools({"latency": "Check queue depth."}, {})
    planner = SequencePlanner([
        {"action": "finish", "summary": "Queue issue", "evidence": ["step:1"]},
        {"action": "search_runbook", "query": "queue"},
        {"action": "finish", "summary": "Check queue depth", "evidence": ["step:2"]},
    ])
    result = agents.run_incident("High latency", planner, tools, max_steps=3)
    assert result["status"] == "completed"
    assert result["evidence"] == ["step:2"]
    assert result["trace"][0]["error"] == "finish must cite successful observation steps"


def test_empty_search_is_not_evidence():
    planner = SequencePlanner([
        {"action": "search_runbook", "query": "unmatched"},
        {"action": "finish", "summary": "No issue", "evidence": ["step:1"]},
    ])
    result = agents.run_incident("High latency", planner,
                                 agents.ReadOnlyTools({"latency": "Check queue depth."}, {}), max_steps=2)
    assert result["status"] == "step_limit"
    assert result["trace"][1]["error"] == "finish must cite successful observation steps"
