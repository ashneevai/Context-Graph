"""
Visualize the Billing Knowledge Graph using matplotlib + networkx.
Run:  python visualize.py
Saves billing_knowledge_graph.png in the current directory.
"""

import matplotlib
matplotlib.use("Agg")          # non-interactive backend – safe everywhere
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

from knowledge_graph import BillingKnowledgeGraph

# ── Color palette by node type ─────────────────────────────────────────────────
TYPE_COLORS = {
    "entity":  "#4A90D9",   # blue
    "process": "#E8A838",   # amber
    "event":   "#E05C5C",   # red
}
DEFAULT_COLOR = "#8E8E8E"


def get_color(node_type: str) -> str:
    return TYPE_COLORS.get(node_type, DEFAULT_COLOR)


def visualize(output_file: str = "billing_knowledge_graph.png"):
    kg = BillingKnowledgeGraph()
    G = kg.graph

    # Layout
    pos = nx.spring_layout(G, seed=42, k=2.8)

    # Node colours
    node_colors = [
        get_color(G.nodes[n].get("type", "")) for n in G.nodes
    ]

    fig, ax = plt.subplots(figsize=(20, 14))
    fig.patch.set_facecolor("#1C1C2E")
    ax.set_facecolor("#1C1C2E")

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#555577",
        arrows=True,
        arrowstyle="-|>",
        arrowsize=18,
        width=1.4,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=20,
        min_target_margin=20,
    )

    # Edge labels (relationship type)
    edge_labels = {
        (u, v): d.get("rel", "") for u, v, d in G.edges(data=True)
    }
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, ax=ax,
        font_size=6.5,
        font_color="#BBBBCC",
        bbox=dict(boxstyle="round,pad=0.15", fc="#1C1C2E", ec="none", alpha=0.7),
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=2200,
        alpha=0.93,
        linewidths=1.5,
        edgecolors="#FFFFFF",
    )

    # Node labels
    nx.draw_networkx_labels(
        G, pos, ax=ax,
        font_size=8.5,
        font_color="white",
        font_weight="bold",
    )

    # Legend
    legend_handles = [
        mpatches.Patch(color=color, label=f"{ntype.capitalize()}")
        for ntype, color in TYPE_COLORS.items()
    ]
    ax.legend(
        handles=legend_handles,
        loc="lower left",
        framealpha=0.3,
        labelcolor="white",
        facecolor="#2A2A3E",
        edgecolor="#555577",
        fontsize=10,
    )

    ax.set_title(
        "Billing Support — Knowledge Context Graph",
        color="white", fontsize=16, fontweight="bold", pad=14,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Graph saved to: {output_file}")


if __name__ == "__main__":
    visualize()
