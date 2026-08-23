"""
Knowledge Graph reasoning for disaster decision support.

Represents relationships between regions, flood risks, populations,
infrastructure, and evacuation policies as a directed graph.

Libraries: NetworkX (local), compatible with Neo4j for production.
"""

import networkx as nx


class DisasterKnowledgeGraph:
    """
    A knowledge graph that encodes domain relationships for
    disaster response reasoning.

    Nodes represent entities (regions, resources, policies).
    Edges represent relationships (has_risk, requires_action, etc.).
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_default_ontology()

    def _build_default_ontology(self):
        """Create the default disaster-response ontology."""

        # ── Resource nodes ───────────────────────────────────────────────
        resources = [
            ("rescue_team", {"type": "resource", "capacity": 50}),
            ("medical_unit", {"type": "resource", "capacity": 30}),
            ("evacuation_bus", {"type": "resource", "capacity": 100}),
            ("shelter", {"type": "resource", "capacity": 500}),
            ("drone_unit", {"type": "resource", "capacity": 5}),
            ("sandbag_supply", {"type": "resource", "capacity": 1000}),
        ]

        # ── Policy nodes ────────────────────────────────────────────────
        policies = [
            ("policy_evacuate", {"type": "policy", "description": "Full evacuation"}),
            ("policy_warn", {"type": "policy", "description": "Issue warning"}),
            ("policy_monitor", {"type": "policy", "description": "Enhanced monitoring"}),
            ("policy_safe", {"type": "policy", "description": "No action needed"}),
        ]

        # ── Risk level nodes ────────────────────────────────────────────
        risk_levels = [
            ("risk_critical", {"type": "risk_level", "threshold": 0.8}),
            ("risk_high", {"type": "risk_level", "threshold": 0.6}),
            ("risk_moderate", {"type": "risk_level", "threshold": 0.4}),
            ("risk_low", {"type": "risk_level", "threshold": 0.0}),
        ]

        self.graph.add_nodes_from(resources + policies + risk_levels)

        # ── Ontology edges: risk → policy → resources ───────────────────
        self.graph.add_edge("risk_critical", "policy_evacuate", relation="triggers")
        self.graph.add_edge("risk_high", "policy_warn", relation="triggers")
        self.graph.add_edge("risk_moderate", "policy_monitor", relation="triggers")
        self.graph.add_edge("risk_low", "policy_safe", relation="triggers")

        self.graph.add_edge("policy_evacuate", "rescue_team", relation="deploys")
        self.graph.add_edge("policy_evacuate", "evacuation_bus", relation="deploys")
        self.graph.add_edge("policy_evacuate", "shelter", relation="deploys")
        self.graph.add_edge("policy_evacuate", "medical_unit", relation="deploys")

        self.graph.add_edge("policy_warn", "rescue_team", relation="alerts")
        self.graph.add_edge("policy_warn", "medical_unit", relation="alerts")

        self.graph.add_edge("policy_monitor", "drone_unit", relation="deploys")
        self.graph.add_edge("policy_monitor", "sandbag_supply", relation="prepares")

    def add_region(self, name, population, elevation, flood_prob=0.0):
        """Add a geographic region node to the knowledge graph."""
        self.graph.add_node(
            name,
            type="region",
            population=population,
            elevation=elevation,
            flood_prob=flood_prob,
        )

        # Link to appropriate risk level
        risk_node = self._classify_risk(flood_prob)
        self.graph.add_edge(name, risk_node, relation="has_risk")

    def update_flood_probability(self, region_name, flood_prob):
        """Update a region's flood probability and re-link risk edges."""
        if region_name not in self.graph:
            return

        self.graph.nodes[region_name]["flood_prob"] = flood_prob

        # Remove old risk edges
        old_edges = [
            (region_name, t) for _, t, d in self.graph.out_edges(region_name, data=True)
            if d.get("relation") == "has_risk"
        ]
        self.graph.remove_edges_from(old_edges)

        # Add new risk edge
        risk_node = self._classify_risk(flood_prob)
        self.graph.add_edge(region_name, risk_node, relation="has_risk")

    def _classify_risk(self, flood_prob):
        """Determine risk level node from flood probability."""
        if flood_prob > 0.8:
            return "risk_critical"
        elif flood_prob > 0.6:
            return "risk_high"
        elif flood_prob > 0.4:
            return "risk_moderate"
        else:
            return "risk_low"

    def query_actions(self, region_name):
        """
        Traverse the knowledge graph to determine actions for a region.

        Path: Region → Risk Level → Policy → Resources

        Returns
        -------
        dict with 'risk_level', 'policy', 'resources'.
        """
        if region_name not in self.graph:
            return {"error": f"Region '{region_name}' not in knowledge graph"}

        result = {
            "region": region_name,
            "region_data": dict(self.graph.nodes[region_name]),
            "risk_level": None,
            "policy": None,
            "resources": [],
            "reasoning_path": [],
        }

        # Step 1: Region → Risk
        for _, risk_node, data in self.graph.out_edges(region_name, data=True):
            if data.get("relation") == "has_risk":
                result["risk_level"] = risk_node
                result["reasoning_path"].append(f"{region_name} --has_risk--> {risk_node}")

                # Step 2: Risk → Policy
                for _, policy_node, pdata in self.graph.out_edges(risk_node, data=True):
                    if pdata.get("relation") == "triggers":
                        result["policy"] = policy_node
                        result["reasoning_path"].append(
                            f"{risk_node} --triggers--> {policy_node}"
                        )

                        # Step 3: Policy → Resources
                        for _, res_node, rdata in self.graph.out_edges(policy_node, data=True):
                            result["resources"].append({
                                "resource": res_node,
                                "action": rdata.get("relation"),
                                "details": dict(self.graph.nodes.get(res_node, {})),
                            })
                            result["reasoning_path"].append(
                                f"{policy_node} --{rdata.get('relation')}--> {res_node}"
                            )
                break

        return result

    def get_all_regions(self):
        """Return all region nodes and their attributes."""
        return {
            n: d for n, d in self.graph.nodes(data=True)
            if d.get("type") == "region"
        }

    def get_graph_summary(self):
        """Return summary statistics of the knowledge graph."""
        nodes_by_type = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("type", "unknown")
            nodes_by_type[t] = nodes_by_type.get(t, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "nodes_by_type": nodes_by_type,
        }
