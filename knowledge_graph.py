import networkx as nx
from typing import List, Dict, Optional


class BillingKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_billing_knowledge()

    def _build_billing_knowledge(self):
        nodes = {
            "Customer": {
                "type": "entity",
                "description": "A person or organization with an account that may hold active subscriptions.",
                "common_issues": [
                    "Unable to access account",
                    "Wrong billing information",
                    "Multiple duplicate accounts",
                    "Account suspended",
                ],
                "solutions": [
                    "Verify identity via registered email",
                    "Update billing info in account settings",
                    "Merge duplicate accounts through admin panel",
                    "Review suspension reason and resolve outstanding balance",
                ],
            },
            "Subscription": {
                "type": "entity",
                "description": "A recurring service agreement between a customer and the company with a defined plan and billing cycle.",
                "common_issues": [
                    "Subscription not activating after payment",
                    "Unexpected auto-cancellation",
                    "Unable to downgrade or upgrade plan",
                    "Wrong plan assigned",
                ],
                "solutions": [
                    "Verify payment status and retry charge",
                    "Review cancellation triggers such as failed payments",
                    "Confirm plan change eligibility and process manually",
                    "Correct plan assignment via admin dashboard",
                ],
            },
            "Invoice": {
                "type": "entity",
                "description": "A billing document issued to a customer for services during a billing period, listing charges, taxes, and discounts.",
                "common_issues": [
                    "Invoice not received by customer",
                    "Incorrect amount on invoice",
                    "Duplicate invoice issued",
                    "Invoice generated after cancellation",
                ],
                "solutions": [
                    "Resend invoice to customer email",
                    "Review line items, apply credit or issue corrected invoice",
                    "Void duplicate invoice and reissue",
                    "Issue refund or account credit for post-cancellation period",
                ],
            },
            "Payment": {
                "type": "process",
                "description": "A financial transaction where a customer pays for their subscription or outstanding balance using a linked payment method.",
                "common_issues": [
                    "Payment declined by bank or card issuer",
                    "Payment not reflected in account balance",
                    "Customer double-charged",
                    "Payment stuck in pending status",
                ],
                "solutions": [
                    "Review decline code, update card details or use alternate method",
                    "Allow 24-48 hours for processing, then escalate to payment gateway",
                    "Identify duplicate transaction and process refund immediately",
                    "Contact payment gateway for pending transaction status",
                ],
            },
            "Refund": {
                "type": "process",
                "description": "A full or partial reversal of a payment that returns funds to the customer, subject to refund policy.",
                "common_issues": [
                    "Refund not received after approval",
                    "Customer disputes partial refund amount",
                    "Refund sent to wrong payment method",
                    "Refund request denied",
                ],
                "solutions": [
                    "Confirm processing time 5-10 business days, escalate if overdue",
                    "Review refund policy and negotiate resolution",
                    "Verify original payment method and reissue to correct method",
                    "Review policy exceptions and escalate to billing manager",
                ],
            },
            "Plan": {
                "type": "entity",
                "description": "A pricing tier defining the features, usage limits, and cost associated with a subscription (e.g. Free, Basic, Pro, Enterprise).",
                "common_issues": [
                    "Features not matching plan description",
                    "Price changed without customer notice",
                    "Unable to change plan",
                    "Trial not converting to paid plan correctly",
                ],
                "solutions": [
                    "Compare plan features in system vs published material and correct",
                    "Check if pricing update notifications were sent, offer goodwill credit",
                    "Verify account eligibility and process change manually",
                    "Review trial settings and manually trigger conversion",
                ],
            },
            "PaymentMethod": {
                "type": "entity",
                "description": "A payment instrument linked to a customer account such as credit card, PayPal, or bank transfer.",
                "common_issues": [
                    "Card expired causing payment failure",
                    "Card declined by issuer",
                    "Cannot add or update payment method",
                    "Wrong default card being charged",
                ],
                "solutions": [
                    "Prompt customer to update card before next billing date",
                    "Try alternate method or advise customer to contact their bank",
                    "Clear browser cache, use incognito, or try a different browser",
                    "Update default payment method in account billing settings",
                ],
            },
            "FailedPayment": {
                "type": "event",
                "description": "A payment attempt that was unsuccessful due to insufficient funds, expired card, bank decline, or network error.",
                "common_issues": [
                    "Repeated consecutive payment failures",
                    "Customer not notified of failed payment",
                    "Service suspended following failure",
                    "Unknown or vague failure reason",
                ],
                "solutions": [
                    "Review failure reason code and guide customer to resolve",
                    "Check notification settings and resend failure alert",
                    "Restore service access upon payment resolution",
                    "Contact payment gateway for detailed failure reason code",
                ],
            },
            "Discount": {
                "type": "entity",
                "description": "A promotional reduction in price applied to a subscription or invoice via a coupon code or automatic promotion.",
                "common_issues": [
                    "Discount code not working at checkout",
                    "Discount not reflected on invoice",
                    "Expired or already-used discount code",
                    "Discount applied to wrong line item",
                ],
                "solutions": [
                    "Verify code validity, expiry date, and eligible plans",
                    "Manually apply discount and regenerate invoice",
                    "Offer alternative active promotion as goodwill gesture",
                    "Review and correct discount allocation on invoice",
                ],
            },
            "Cancellation": {
                "type": "process",
                "description": "The termination of a subscription, either by customer request or triggered automatically by system events like repeated failed payments.",
                "common_issues": [
                    "Accidental self-cancellation",
                    "Charged after cancellation date",
                    "Data or content lost after cancellation",
                    "Cancellation request not processing",
                ],
                "solutions": [
                    "Reactivate subscription within grace period if eligible",
                    "Issue refund for any post-cancellation charges",
                    "Check data retention policy and restore if within window",
                    "Force cancel via admin system and confirm with customer",
                ],
            },
            "Chargeback": {
                "type": "event",
                "description": "A dispute initiated by a customer through their bank to reverse a charge, bypassing the normal refund process.",
                "common_issues": [
                    "Fraudulent or unrecognized chargeback",
                    "Legitimate chargeback not being processed",
                    "Account suspended due to open chargeback",
                    "Multiple chargebacks from same customer",
                ],
                "solutions": [
                    "Gather transaction evidence and submit dispute response within deadline",
                    "Escalate to payments team for manual processing",
                    "Review account, resolve underlying issue to lift suspension",
                    "Flag account for fraud review and escalate to risk team",
                ],
            },
            "Tax": {
                "type": "entity",
                "description": "Government-mandated charges applied to invoices based on customer location, local jurisdiction, and service classification.",
                "common_issues": [
                    "Incorrect tax rate applied to invoice",
                    "Tax-exempt customer incorrectly charged tax",
                    "Customer needs formal tax invoice with VAT breakdown",
                    "VAT number not recognized or validated",
                ],
                "solutions": [
                    "Update customer billing address and recalculate tax",
                    "Apply tax exemption certificate and issue credit for overpaid tax",
                    "Generate formal tax invoice with full VAT details",
                    "Manually validate and enter VAT number in tax settings",
                ],
            },
            "BillingCycle": {
                "type": "process",
                "description": "The recurring time period (monthly or annual) during which service charges are assessed and invoices are generated.",
                "common_issues": [
                    "Incorrect billing anchor date",
                    "Customer confused about prorated charges",
                    "Discrepancy between annual and monthly charge amounts",
                    "Billing cycle misaligned with customer expectations",
                ],
                "solutions": [
                    "Adjust billing anchor date in subscription settings",
                    "Explain proration formula clearly with examples",
                    "Review plan pricing and confirm correct billing frequency applied",
                    "Align billing cycle start date to customer preference",
                ],
            },
            "Credit": {
                "type": "entity",
                "description": "A monetary balance held on a customer account, automatically applied to offset future invoices.",
                "common_issues": [
                    "Credit not applied automatically to invoice",
                    "Credit expired before being used",
                    "Incorrect credit amount issued",
                    "Credit balance not visible in customer portal",
                ],
                "solutions": [
                    "Manually apply credit to current open invoice",
                    "Review expiry policy and extend if warranted by circumstance",
                    "Correct credit amount and adjust affected invoice",
                    "Sync account balance display in customer portal",
                ],
            },
            "UsageOverage": {
                "type": "event",
                "description": "Additional charges incurred when a customer's usage exceeds their plan's included limits during a billing period.",
                "common_issues": [
                    "Unexpected high overage charges on invoice",
                    "Not notified before overage threshold was reached",
                    "Overage calculation appears incorrect",
                    "Customer disputes legitimacy of overage charges",
                ],
                "solutions": [
                    "Pull usage logs and walk customer through charges",
                    "Configure usage alert thresholds for the customer",
                    "Audit overage calculation and apply credit if error found",
                    "Offer plan upgrade to eliminate overage risk going forward",
                ],
            },
            "SupportTicket": {
                "type": "process",
                "description": "A formal record of a customer billing inquiry or issue, used to track resolution from open to closed.",
                "common_issues": [
                    "Ticket not responded to within SLA",
                    "Recurring issue after ticket marked resolved",
                    "Ticket routed to wrong team",
                    "Urgent issue not escalated appropriately",
                ],
                "solutions": [
                    "Escalate overdue tickets to senior billing agent",
                    "Reopen ticket, investigate root cause, and implement permanent fix",
                    "Reassign to billing specialist team",
                    "Flag as high priority and trigger escalation workflow",
                ],
            },
        }

        for name, attrs in nodes.items():
            self.graph.add_node(name, **attrs)

        edges = [
            # Customer
            ("Customer", "Subscription",   {"rel": "has",           "desc": "A customer can hold one or more active subscriptions"}),
            ("Customer", "PaymentMethod",  {"rel": "owns",          "desc": "Customers link payment methods to their billing account"}),
            ("Customer", "Invoice",        {"rel": "receives",      "desc": "Invoices are issued to and received by customers"}),
            ("Customer", "SupportTicket",  {"rel": "creates",       "desc": "Customers open support tickets for billing inquiries"}),
            ("Customer", "Credit",         {"rel": "holds",         "desc": "Account credit balance belongs to the customer"}),
            ("Customer", "Discount",       {"rel": "applies",       "desc": "Customers apply discount codes at checkout or renewal"}),
            # Subscription
            ("Subscription", "Plan",          {"rel": "belongs_to",    "desc": "Each subscription is tied to a specific pricing plan"}),
            ("Subscription", "Invoice",       {"rel": "generates",     "desc": "Subscriptions generate invoices each billing cycle"}),
            ("Subscription", "BillingCycle",  {"rel": "follows",       "desc": "Subscriptions operate on a defined billing cycle"}),
            ("Subscription", "Cancellation",  {"rel": "can_trigger",   "desc": "Subscriptions can be cancelled by customer or system"}),
            ("Subscription", "UsageOverage",  {"rel": "can_incur",     "desc": "Subscriptions may incur overage charges beyond plan limits"}),
            # Invoice
            ("Invoice", "Payment",       {"rel": "requires",      "desc": "Invoices must be settled by the due date via payment"}),
            ("Invoice", "Tax",           {"rel": "includes",      "desc": "Invoices include applicable government taxes"}),
            ("Invoice", "Discount",      {"rel": "may_include",   "desc": "Discounts reduce the invoice total amount"}),
            ("Invoice", "Credit",        {"rel": "may_apply",     "desc": "Account credit is applied automatically to invoice balance"}),
            ("Invoice", "UsageOverage",  {"rel": "may_include",   "desc": "Invoices can include overage charges for that billing period"}),
            # Payment
            ("Payment", "PaymentMethod",  {"rel": "uses",          "desc": "Payments are processed using a linked payment method"}),
            ("Payment", "Refund",         {"rel": "can_generate",  "desc": "Payments can be fully or partially refunded"}),
            ("Payment", "FailedPayment",  {"rel": "can_become",    "desc": "A payment attempt may fail and become a FailedPayment event"}),
            ("Payment", "Chargeback",     {"rel": "can_trigger",   "desc": "Customers may dispute a payment causing a chargeback"}),
            # Failed Payment
            ("FailedPayment", "Subscription",  {"rel": "risks",      "desc": "Repeated failures risk subscription suspension or cancellation"}),
            ("FailedPayment", "SupportTicket", {"rel": "generates",  "desc": "Failed payments typically generate support tickets"}),
            # Refund
            ("Refund", "Invoice",  {"rel": "relates_to",  "desc": "Refunds are linked to the original invoice or payment"}),
            ("Refund", "Credit",   {"rel": "can_become",  "desc": "Refunds can be issued as account credit instead of cash return"}),
            # Cancellation
            ("Cancellation", "Refund",        {"rel": "may_trigger",   "desc": "Cancellations within the refund window may trigger refunds"}),
            ("Cancellation", "Subscription",  {"rel": "terminates",    "desc": "Cancellation ends the active subscription"}),
            # Chargeback
            ("Chargeback", "Subscription",   {"rel": "can_suspend",  "desc": "Chargebacks can trigger account or subscription suspension"}),
            ("Chargeback", "SupportTicket",  {"rel": "creates",      "desc": "Chargebacks create urgent high-priority support tickets"}),
            # Plan
            ("Plan", "BillingCycle",  {"rel": "defines",       "desc": "Plans define the billing frequency and cycle terms"}),
            ("Plan", "Discount",      {"rel": "eligible_for",  "desc": "Certain plans qualify for specific promotional discounts"}),
        ]

        for source, target, attrs in edges:
            self.graph.add_edge(source, target, **attrs)

    # ── Query helpers ──────────────────────────────────────────────────────────

    def get_node_info(self, node: str) -> Optional[Dict]:
        return dict(self.graph.nodes[node]) if node in self.graph.nodes else None

    def get_all_node_names(self) -> List[str]:
        return list(self.graph.nodes())

    def get_neighbors(self, node: str) -> List[str]:
        if node not in self.graph.nodes:
            return []
        return list(set(list(self.graph.successors(node)) + list(self.graph.predecessors(node))))

    def find_path(self, source: str, target: str) -> List[str]:
        try:
            return nx.shortest_path(self.graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_context_for_entities(self, entity_names: List[str]) -> str:
        """Build a rich context string from graph nodes for the given entities."""
        parts: List[str] = []
        visited: set = set()

        for entity in entity_names:
            if entity not in self.graph.nodes or entity in visited:
                continue
            visited.add(entity)
            data = self.graph.nodes[entity]

            parts.append(f"\n## {entity} ({data.get('type', 'concept')})")
            parts.append(f"Description: {data.get('description', '')}")

            if data.get("common_issues"):
                parts.append("Common Issues:")
                for issue in data["common_issues"]:
                    parts.append(f"  - {issue}")

            if data.get("solutions"):
                parts.append("Solutions:")
                for sol in data["solutions"]:
                    parts.append(f"  - {sol}")

            # Outgoing relationships
            out_edges = [(t, self.graph[entity][t]) for t in self.graph.successors(entity)]
            if out_edges:
                parts.append("Relationships:")
                for target, edge_data in out_edges:
                    parts.append(f"  - [{edge_data.get('rel', 'related_to')}] → {target}: {edge_data.get('desc', '')}")

            # One-level-deep neighbours not already queued
            unvisited = [n for n in self.get_neighbors(entity) if n not in visited and n not in entity_names]
            for neighbor in unvisited[:3]:
                n_data = self.graph.nodes[neighbor]
                parts.append(f"\n### Related: {neighbor}")
                parts.append(f"  {n_data.get('description', '')}")

        return "\n".join(parts)

    def get_graph_summary(self) -> str:
        nodes = self.get_all_node_names()
        return (
            f"Billing Knowledge Graph  |  {len(nodes)} entities  |  "
            f"{self.graph.number_of_edges()} relationships\n"
            f"Entities: {', '.join(nodes)}"
        )
