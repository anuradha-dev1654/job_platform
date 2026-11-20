from .graph import build_graph

_graph = build_graph()  # compiled once


def run(state: dict) -> dict:
    return _graph.invoke(state)
