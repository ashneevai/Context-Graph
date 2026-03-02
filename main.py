import sys
from groq_agent import BillingSupportAgent

DIVIDER = "─" * 60

HELP_TEXT = """
Commands:
  help          Show this help message
  graph         Display knowledge graph summary
  entities      List all billing entities in the graph
  path A B      Show relationship path between two entities
  reset         Clear conversation history
  quit / exit   Exit the agent
"""

SAMPLE_QUERIES = [
    "My payment was declined and my subscription got cancelled. What do I do?",
    "I was charged twice on the same invoice.",
    "How long does a refund take to process?",
    "My discount code is not working at checkout.",
    "I was charged tax even though I submitted a tax exemption certificate.",
]


def print_banner():
    print(DIVIDER)
    print("  Billing Support Agent")
    print("  Knowledge Context Graph  ×  Groq LLM")
    print(DIVIDER)


def print_sample_queries():
    print("\nSample questions to try:")
    for i, q in enumerate(SAMPLE_QUERIES, 1):
        print(f"  {i}. {q}")
    print()


def run():
    print_banner()

    try:
        agent = BillingSupportAgent()
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    print(f"\n{agent.kg.get_graph_summary()}")
    print_sample_queries()
    print(f"Type 'help' for commands.\n{DIVIDER}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit"):
            print("Goodbye!")
            break

        if cmd == "help":
            print(HELP_TEXT)
            continue

        if cmd == "graph":
            print(f"\n{agent.kg.get_graph_summary()}\n")
            continue

        if cmd == "entities":
            nodes = agent.kg.get_all_node_names()
            print(f"\nBilling entities ({len(nodes)}):")
            for n in sorted(nodes):
                info = agent.kg.get_node_info(n)
                print(f"  • {n:20s} — {info.get('description', '')[:70]}...")
            print()
            continue

        if cmd.startswith("path "):
            parts = user_input.split()
            if len(parts) == 3:
                path = agent.kg.find_path(parts[1], parts[2])
                if path:
                    print(f"\nPath: {' → '.join(path)}\n")
                else:
                    print(f"\nNo path found between '{parts[1]}' and '{parts[2]}'.\n")
            else:
                print("Usage: path <EntityA> <EntityB>\n")
            continue

        if cmd == "reset":
            agent.reset_conversation()
            print("Conversation history cleared.\n")
            continue

        # ── Normal query ──
        try:
            response, entities = agent.answer(user_input)
            if entities:
                print(f"\n[Graph context: {', '.join(entities)}]")
            print(f"\nAgent: {response}\n{DIVIDER}\n")
        except Exception as e:
            print(f"\n[ERROR] {e}\n")


if __name__ == "__main__":
    run()
