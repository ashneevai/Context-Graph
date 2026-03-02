import os
import json
from groq import Groq
from dotenv import load_dotenv
from knowledge_graph import BillingKnowledgeGraph

load_dotenv()


class BillingSupportAgent:
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY not set. Please add it to your .env file.")
        self.client = Groq(api_key=api_key)
        self.kg = BillingKnowledgeGraph()
        self.conversation_history: list[dict] = []

    # ── Entity extraction ──────────────────────────────────────────────────────

    def extract_entities(self, query: str) -> list[str]:
        """Ask Groq to identify which billing graph nodes are relevant to the query."""
        all_nodes = self.kg.get_all_node_names()
        prompt = (
            f"You are a billing support classifier.\n"
            f"Available billing entities: {', '.join(all_nodes)}\n\n"
            f"Customer query: \"{query}\"\n\n"
            f"Return ONLY a JSON array (max 5) of the most relevant entity names from the list above.\n"
            f"Example: [\"Invoice\", \"Payment\", \"Refund\"]\n"
            f"Do not include any other text."
        )

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=150,
        )
        content = response.choices[0].message.content.strip()

        # Parse JSON array from response
        try:
            start, end = content.find("["), content.rfind("]") + 1
            if start != -1 and end > start:
                candidates = json.loads(content[start:end])
                return [e for e in candidates if e in all_nodes]
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: keyword match
        return [n for n in all_nodes if n.lower() in query.lower()]

    # ── Answer generation ──────────────────────────────────────────────────────

    def answer(self, query: str) -> tuple[str, list[str]]:
        """
        Respond to a billing support query using knowledge-graph context.

        Returns:
            (response_text, entities_used)
        """
        entities = self.extract_entities(query)

        if entities:
            graph_context = self.kg.get_context_for_entities(entities)
        else:
            # Generic fallback context
            graph_context = self.kg.get_context_for_entities(["Customer", "Invoice", "Payment"])

        system_prompt = (
            "You are an expert billing support agent.\n"
            "Use the knowledge graph context below to provide accurate, empathetic, and actionable responses.\n\n"
            f"KNOWLEDGE GRAPH CONTEXT:\n{graph_context}\n\n"
            "Guidelines:\n"
            "- Be empathetic and professional\n"
            "- Provide specific, numbered steps when possible\n"
            "- Mention escalation paths when needed\n"
            "- Keep responses concise but complete\n"
            "- If the issue is outside your scope, say so clearly"
        )

        self.conversation_history.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[{"role": "system", "content": system_prompt}] + self.conversation_history,
            temperature=0.7,
            max_tokens=800,
        )

        reply = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply, entities

    def reset_conversation(self):
        self.conversation_history = []
