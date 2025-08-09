from master_ai.core.task_graph import TaskGraph


def test_graph_runs_in_order():
    order = []
    tg = TaskGraph()
    tg.add("a", lambda: order.append("a"))
    tg.add("b", lambda: order.append("b"))
    tg.execute()
    assert order == ["a", "b"]
