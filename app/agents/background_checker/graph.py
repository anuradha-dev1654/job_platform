from langgraph.graph import StateGraph, END
from .state import CheckState
from .nodes import github_node, linkedin_node, report_node


def build_graph():
    g = StateGraph(CheckState)
    g.add_node("github", github_node)
    g.add_node("linkedin", linkedin_node)
    g.add_node("report", report_node)
    g.set_entry_point("github")
    g.add_edge("github", "linkedin")
    g.add_edge("linkedin", "report")
    g.add_edge("report", END)
    return g.compile()
