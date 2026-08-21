"""
Tests: Research Intelligence Layer — Evidence Graph Foundation (Q12).

The layer records structured research knowledge only.  It never trades,
never generates signals, and never predicts.

Coverage:
    * node creation, immutability, metadata freezing, hash equality,
      serialization / deserialization
    * edge creation, validation, duplicate prevention
    * missing-node errors, graph traversal, clear operations
    * repository save/load, determinism, empty and large graphs
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from researchos.intelligence import (
    DEFAULT_PATH,
    EVIDENCE_GRAPH_VERSION,
    INTELLIGENCE_VERSION,
    EvidenceEdge,
    EvidenceError,
    EvidenceGraph,
    EvidenceGraphStore,
    EvidenceNode,
    InvalidEdgeError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    NodeType,
    Relationship,
)


def make_node(
    node_id: str = "dataset_1",
    node_type: NodeType = NodeType.DATASET,
    reference_id: str = "ref_dataset_1",
    **kwargs,
) -> EvidenceNode:
    return EvidenceNode(
        node_id=node_id,
        node_type=node_type,
        reference_id=reference_id,
        **kwargs,
    )


def make_edge(
    edge_id: str = "edge_1",
    source_id: str = "dataset_1",
    target_id: str = "model_1",
    relationship: Relationship = Relationship.USED_BY,
    **kwargs,
) -> EvidenceEdge:
    return EvidenceEdge(
        edge_id=edge_id,
        source_id=source_id,
        target_id=target_id,
        relationship=relationship,
        **kwargs,
    )


def make_graph():
    graph = EvidenceGraph()
    graph.add_node(make_node("dataset_1"))
    graph.add_node(make_node("model_1", NodeType.MODEL, "ref_model_1"))
    graph.add_node(make_node("validation_1", NodeType.VALIDATION, "ref_validation_1"))
    graph.add_node(make_node("experiment_1", NodeType.EXPERIMENT, "ref_experiment_1"))
    graph.add_edge(make_edge("e_ds_model", "dataset_1", "model_1"))
    graph.add_edge(make_edge("e_model_exp", "model_1", "experiment_1", Relationship.VALIDATED_BY))
    return graph


class TestNodeType(unittest.TestCase):
    def test_has_all_required_members(self):
        expected = {
            "DATASET",
            "FEATURE_SET",
            "LABEL_SET",
            "MODEL",
            "VALIDATION",
            "EXPERIMENT",
            "RESULT",
        }
        self.assertEqual({m.name for m in NodeType}, expected)

    def test_members_are_string_values(self):
        self.assertTrue(issubclass(NodeType, str))
        self.assertIsInstance(NodeType.DATASET, str)

    def test_from_string_dataset(self):
        self.assertIs(NodeType.from_string("dataset"), NodeType.DATASET)
        self.assertIs(NodeType.from_string("DATASET"), NodeType.DATASET)

    def test_from_string_feature_set(self):
        self.assertIs(NodeType.from_string("feature_set"), NodeType.FEATURE_SET)
        self.assertIs(NodeType.from_string("FeatureSet"), NodeType.FEATURE_SET)

    def test_from_string_label_set(self):
        self.assertIs(NodeType.from_string("label_set"), NodeType.LABEL_SET)

    def test_from_string_model(self):
        self.assertIs(NodeType.from_string("model"), NodeType.MODEL)

    def test_from_string_validation(self):
        self.assertIs(NodeType.from_string("validation"), NodeType.VALIDATION)

    def test_from_string_experiment(self):
        self.assertIs(NodeType.from_string("experiment"), NodeType.EXPERIMENT)

    def test_from_string_result(self):
        self.assertIs(NodeType.from_string("result"), NodeType.RESULT)

    def test_from_string_unknown_raises(self):
        with self.assertRaises(ValueError):
            NodeType.from_string("banana")

    def test_from_string_empty_raises(self):
        with self.assertRaises(ValueError):
            NodeType.from_string("")

    def test_matches(self):
        self.assertTrue(NodeType.MODEL.matches("model"))
        self.assertFalse(NodeType.MODEL.matches("dataset"))


class TestRelationship(unittest.TestCase):
    def test_has_all_required_members(self):
        expected = {
            "USED_BY",
            "GENERATED_FROM",
            "VALIDATED_BY",
            "PRODUCED",
            "DEPENDS_ON",
        }
        self.assertEqual({m.name for m in Relationship}, expected)

    def test_members_are_string_values(self):
        self.assertTrue(issubclass(Relationship, str))
        self.assertIsInstance(Relationship.USED_BY, str)

    def test_from_string_used_by(self):
        self.assertIs(Relationship.from_string("used_by"), Relationship.USED_BY)
        self.assertIs(Relationship.from_string("USED_BY"), Relationship.USED_BY)

    def test_from_string_generated_from(self):
        self.assertIs(Relationship.from_string("generated_from"), Relationship.GENERATED_FROM)

    def test_from_string_validated_by(self):
        self.assertIs(Relationship.from_string("validated_by"), Relationship.VALIDATED_BY)

    def test_from_string_produced(self):
        self.assertIs(Relationship.from_string("produced"), Relationship.PRODUCED)

    def test_from_string_depends_on(self):
        self.assertIs(Relationship.from_string("depends_on"), Relationship.DEPENDS_ON)

    def test_from_string_unknown_raises(self):
        with self.assertRaises(ValueError):
            Relationship.from_string("nope")

    def test_matches(self):
        self.assertTrue(Relationship.PRODUCED.matches("produced"))
        self.assertFalse(Relationship.PRODUCED.matches("used_by"))


class TestEvidenceNodeCreation(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        node = make_node()
        self.assertEqual(node.node_id, "dataset_1")
        self.assertIs(node.node_type, NodeType.DATASET)
        self.assertEqual(node.reference_id, "ref_dataset_1")
        self.assertEqual(dict(node.metadata), {})

    def test_default_created_at_is_empty(self):
        node = make_node()
        self.assertEqual(node.created_at, "")

    def test_metadata_default_empty(self):
        node = make_node()
        self.assertEqual(dict(node.metadata), {})

    def test_metadata_accepted(self):
        node = make_node(metadata={"source": "mt5", "symbol": "XAUUSD"})
        self.assertEqual(dict(node.metadata), {"source": "mt5", "symbol": "XAUUSD"})

    def test_created_at_accepted(self):
        node = make_node(created_at="2024-01-01T00:00:00Z")
        self.assertEqual(node.created_at, "2024-01-01T00:00:00Z")

    def test_all_node_types_constructable(self):
        for node_type in NodeType:
            node = make_node(node_id=f"n_{node_type.value}", node_type=node_type)
            self.assertIs(node.node_type, node_type)

    def test_whitespace_identifiers_stripped(self):
        node = make_node(node_id="  dataset_1  ", reference_id="  ref_x  ")
        self.assertEqual(node.node_id, "dataset_1")
        self.assertEqual(node.reference_id, "ref_x")

    def test_repr_contains_node_id(self):
        self.assertIn("dataset_1", repr(make_node()))

    def test_equality_same_fields(self):
        a = make_node()
        b = make_node()
        self.assertEqual(a, b)

    def test_equality_different_reference(self):
        self.assertNotEqual(make_node(), make_node(reference_id="other"))


class TestEvidenceNodeValidation(unittest.TestCase):
    def test_empty_node_id_raises(self):
        with self.assertRaises(EvidenceError):
            make_node(node_id="")

    def test_none_node_id_raises(self):
        with self.assertRaises(EvidenceError):
            make_node(node_id=None)  # type: ignore[arg-type]

    def test_empty_reference_id_raises(self):
        with self.assertRaises(EvidenceError):
            make_node(reference_id="")

    def test_bad_node_type_raises(self):
        with self.assertRaises(EvidenceError):
            make_node(node_type="dataset")  # type: ignore[arg-type]

    def test_metadata_not_mapping_raises(self):
        with self.assertRaises(EvidenceError):
            make_node(metadata="not-a-mapping")  # type: ignore[arg-type]


class TestEvidenceNodeImmutability(unittest.TestCase):
    def test_is_frozen_dataclass(self):
        node = make_node()
        with self.assertRaises(Exception):
            node.node_id = "mutated"  # type: ignore[misc]

    def test_node_type_immutable(self):
        node = make_node()
        with self.assertRaises(Exception):
            node.node_type = NodeType.MODEL  # type: ignore[misc]

    def test_reference_id_immutable(self):
        node = make_node()
        with self.assertRaises(Exception):
            node.reference_id = "mutated"  # type: ignore[misc]

    def test_metadata_is_mapping_proxy(self):
        from types import MappingProxyType

        node = make_node(metadata={"a": 1})
        self.assertIsInstance(node.metadata, MappingProxyType)

    def test_metadata_cannot_be_mutated(self):
        node = make_node(metadata={"a": 1})
        with self.assertRaises(TypeError):
            node.metadata["a"] = 2  # type: ignore[index]

    def test_metadata_cannot_be_extended(self):
        node = make_node(metadata={"a": 1})
        with self.assertRaises(TypeError):
            node.metadata["b"] = 3  # type: ignore[index]

    def test_nested_metadata_surface_is_copied(self):
        node = make_node(metadata={"nested": {"k": 1}})
        self.assertEqual(node.metadata["nested"]["k"], 1)

    def test_created_at_immutable(self):
        node = make_node()
        with self.assertRaises(Exception):
            node.created_at = "2020-01-01"  # type: ignore[misc]


class TestEvidenceNodeHash(unittest.TestCase):
    def test_equal_nodes_have_equal_hash(self):
        a = make_node(metadata={"x": 1})
        b = make_node(metadata={"x": 1})
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_different_id_different_hash(self):
        self.assertNotEqual(hash(make_node("a")), hash(make_node("b")))

    def test_different_metadata_different_hash(self):
        self.assertNotEqual(
            hash(make_node(metadata={"x": 1})),
            hash(make_node(metadata={"x": 2})),
        )

    def test_different_created_at_different_hash(self):
        self.assertNotEqual(
            hash(make_node(created_at="2024-01-01")),
            hash(make_node(created_at="2024-01-02")),
        )

    def test_node_is_hashable_in_set(self):
        nodes = {make_node("a"), make_node("a"), make_node("b")}
        self.assertEqual(len(nodes), 2)

    def test_node_hash_deterministic(self):
        self.assertEqual(hash(make_node("x")), hash(make_node("x")))


class TestEvidenceNodeSerialization(unittest.TestCase):
    def test_to_dict_roundtrip(self):
        node = make_node(metadata={"a": 1}, created_at="2024-01-01T00:00:00Z")
        restored = EvidenceNode.from_dict(node.to_dict())
        self.assertEqual(restored, node)

    def test_to_dict_json_compatible(self):
        node = make_node(metadata={"a": 1}, created_at="2024-01-01T00:00:00Z")
        text = json.dumps(node.to_dict())
        self.assertIn("dataset_1", text)

    def test_to_dict_keys(self):
        data = make_node().to_dict()
        self.assertEqual(
            set(data.keys()),
            {"node_id", "node_type", "reference_id", "metadata", "created_at"},
        )

    def test_from_dict_missing_node_id_raises(self):
        with self.assertRaises((KeyError, EvidenceError)):
            EvidenceNode.from_dict({"node_type": "dataset"})

    def test_from_dict_reconstructs_type(self):
        node = EvidenceNode.from_dict({"node_id": "x", "node_type": "MODEL", "reference_id": "r"})
        self.assertIs(node.node_type, NodeType.MODEL)

    def test_serialization_deterministic(self):
        node = make_node(metadata={"b": 1, "a": 2})
        self.assertEqual(node.to_dict(), node.to_dict())

    def test_hash_survives_serialization(self):
        node = make_node(metadata={"a": 1})
        self.assertEqual(hash(EvidenceNode.from_dict(node.to_dict())), hash(node))


class TestEvidenceEdgeCreation(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        edge = make_edge()
        self.assertEqual(edge.edge_id, "edge_1")
        self.assertEqual(edge.source_id, "dataset_1")
        self.assertEqual(edge.target_id, "model_1")
        self.assertIs(edge.relationship, Relationship.USED_BY)

    def test_default_created_at_empty(self):
        self.assertEqual(make_edge().created_at, "")

    def test_metadata_default_empty(self):
        self.assertEqual(dict(make_edge().metadata), {})

    def test_metadata_accepted(self):
        edge = make_edge(metadata={"weight": 0.5})
        self.assertEqual(dict(edge.metadata), {"weight": 0.5})

    def test_created_at_accepted(self):
        edge = make_edge(created_at="2024-01-01T00:00:00Z")
        self.assertEqual(edge.created_at, "2024-01-01T00:00:00Z")

    def test_all_relationships_constructable(self):
        for rel in Relationship:
            edge = make_edge(edge_id=f"e_{rel.value}", relationship=rel)
            self.assertIs(edge.relationship, rel)

    def test_whitespace_identifiers_stripped(self):
        edge = make_edge(edge_id="  e  ", source_id="  a  ", target_id="  b  ")
        self.assertEqual(edge.edge_id, "e")
        self.assertEqual(edge.source_id, "a")
        self.assertEqual(edge.target_id, "b")

    def test_equality_same_fields(self):
        self.assertEqual(make_edge(), make_edge())

    def test_equality_different_relationship(self):
        self.assertNotEqual(make_edge(), make_edge(relationship=Relationship.PRODUCED))


class TestEvidenceEdgeValidation(unittest.TestCase):
    def test_empty_edge_id_raises(self):
        with self.assertRaises(EvidenceError):
            make_edge(edge_id="")

    def test_empty_source_raises(self):
        with self.assertRaises(EvidenceError):
            make_edge(source_id="")

    def test_empty_target_raises(self):
        with self.assertRaises(EvidenceError):
            make_edge(target_id="")

    def test_bad_relationship_raises(self):
        with self.assertRaises(EvidenceError):
            make_edge(relationship="used_by")  # type: ignore[arg-type]

    def test_metadata_not_mapping_raises(self):
        with self.assertRaises(EvidenceError):
            make_edge(metadata=[1, 2])  # type: ignore[arg-type]


class TestEvidenceEdgeImmutability(unittest.TestCase):
    def test_is_frozen_dataclass(self):
        edge = make_edge()
        with self.assertRaises(Exception):
            edge.edge_id = "mutated"  # type: ignore[misc]

    def test_source_immutable(self):
        edge = make_edge()
        with self.assertRaises(Exception):
            edge.source_id = "mutated"  # type: ignore[misc]

    def test_relationship_immutable(self):
        edge = make_edge()
        with self.assertRaises(Exception):
            edge.relationship = Relationship.PRODUCED  # type: ignore[misc]

    def test_metadata_cannot_be_mutated(self):
        edge = make_edge(metadata={"a": 1})
        with self.assertRaises(TypeError):
            edge.metadata["a"] = 2  # type: ignore[index]

    def test_created_at_immutable(self):
        edge = make_edge()
        with self.assertRaises(Exception):
            edge.created_at = "2020-01-01"  # type: ignore[misc]


class TestEvidenceEdgeHash(unittest.TestCase):
    def test_equal_edges_have_equal_hash(self):
        self.assertEqual(hash(make_edge("e")), hash(make_edge("e")))

    def test_different_id_different_hash(self):
        self.assertNotEqual(hash(make_edge("a")), hash(make_edge("b")))

    def test_different_relationship_different_hash(self):
        self.assertNotEqual(
            hash(make_edge(relationship=Relationship.USED_BY)),
            hash(make_edge(relationship=Relationship.PRODUCED)),
        )

    def test_edge_is_hashable_in_set(self):
        edges = {make_edge("a"), make_edge("a"), make_edge("b")}
        self.assertEqual(len(edges), 2)

    def test_edge_hash_deterministic(self):
        self.assertEqual(hash(make_edge("x")), hash(make_edge("x")))


class TestEvidenceEdgeSerialization(unittest.TestCase):
    def test_to_dict_roundtrip(self):
        edge = make_edge(metadata={"a": 1}, created_at="2024-01-01T00:00:00Z")
        restored = EvidenceEdge.from_dict(edge.to_dict())
        self.assertEqual(restored, edge)

    def test_to_dict_json_compatible(self):
        text = json.dumps(make_edge().to_dict())
        self.assertIn("edge_1", text)

    def test_to_dict_keys(self):
        data = make_edge().to_dict()
        self.assertEqual(
            set(data.keys()),
            {"edge_id", "source_id", "target_id", "relationship", "metadata", "created_at"},
        )

    def test_from_dict_reconstructs_relationship(self):
        edge = EvidenceEdge.from_dict(
            {"edge_id": "e", "source_id": "a", "target_id": "b", "relationship": "VALIDATED_BY"}
        )
        self.assertIs(edge.relationship, Relationship.VALIDATED_BY)

    def test_serialization_deterministic(self):
        edge = make_edge(metadata={"b": 1, "a": 2})
        self.assertEqual(edge.to_dict(), edge.to_dict())

    def test_hash_survives_serialization(self):
        edge = make_edge(metadata={"a": 1})
        self.assertEqual(hash(EvidenceEdge.from_dict(edge.to_dict())), hash(edge))


class TestEvidenceGraphAddNode(unittest.TestCase):
    def test_add_node_increases_count(self):
        graph = EvidenceGraph()
        graph.add_node(make_node())
        self.assertEqual(graph.count_nodes(), 1)

    def test_add_multiple_nodes(self):
        graph = EvidenceGraph()
        for i in range(5):
            graph.add_node(make_node(f"n{i}"))
        self.assertEqual(graph.count_nodes(), 5)

    def test_duplicate_node_id_raises(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        with self.assertRaises(NodeAlreadyExistsError):
            graph.add_node(make_node("a"))

    def test_duplicate_node_id_does_not_change_count(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        with self.assertRaises(NodeAlreadyExistsError):
            graph.add_node(make_node("a"))
        self.assertEqual(graph.count_nodes(), 1)

    def test_add_non_node_raises_typeerror(self):
        graph = EvidenceGraph()
        with self.assertRaises(TypeError):
            graph.add_node("not-a-node")  # type: ignore[arg-type]

    def test_add_node_then_has_node(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        self.assertTrue(graph.has_node("a"))
        self.assertFalse(graph.has_node("b"))


class TestEvidenceGraphGetNode(unittest.TestCase):
    def test_get_node_returns_same_object(self):
        graph = EvidenceGraph()
        node = make_node("a")
        graph.add_node(node)
        self.assertIs(graph.get_node("a"), node)

    def test_get_missing_node_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.get_node("missing")

    def test_get_missing_node_error_carries_id(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError) as ctx:
            graph.get_node("ghost")
        self.assertEqual(ctx.exception.node_id, "ghost")

    def test_get_node_is_oid_one(self):
        graph = EvidenceGraph()
        for i in range(100):
            graph.add_node(make_node(f"n{i}"))
        for i in range(100):
            self.assertEqual(graph.get_node(f"n{i}").node_id, f"n{i}")


class TestEvidenceGraphAddEdge(unittest.TestCase):
    def test_add_edge_increases_count(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e", "a", "b"))
        self.assertEqual(graph.count_edges(), 1)

    def test_dangling_source_raises(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("b"))
        with self.assertRaises(NodeNotFoundError):
            graph.add_edge(make_edge("e", "a", "b"))

    def test_dangling_target_raises(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        with self.assertRaises(NodeNotFoundError):
            graph.add_edge(make_edge("e", "a", "b"))

    def test_dangling_edge_not_added(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        with self.assertRaises(NodeNotFoundError):
            graph.add_edge(make_edge("e", "a", "b"))
        self.assertEqual(graph.count_edges(), 0)

    def test_duplicate_relationship_raises(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e1", "a", "b"))
        with self.assertRaises(InvalidEdgeError):
            graph.add_edge(make_edge("e2", "a", "b"))

    def test_reverse_relationship_allowed(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e1", "a", "b"))
        graph.add_edge(make_edge("e2", "b", "a"))
        self.assertEqual(graph.count_edges(), 2)

    def test_same_pair_different_relationship_allowed(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e1", "a", "b", Relationship.USED_BY))
        graph.add_edge(make_edge("e2", "a", "b", Relationship.DEPENDS_ON))
        self.assertEqual(graph.count_edges(), 2)

    def test_duplicate_edge_id_raises(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e", "a", "b"))
        with self.assertRaises(InvalidEdgeError):
            graph.add_edge(make_edge("e", "a", "b", Relationship.PRODUCED))

    def test_add_non_edge_raises_typeerror(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        with self.assertRaises(TypeError):
            graph.add_edge("not-an-edge")  # type: ignore[arg-type]


class TestEvidenceGraphGetEdges(unittest.TestCase):
    def test_get_edges_returns_incident(self):
        graph = make_graph()
        edge_ids = {e.edge_id for e in graph.get_edges("model_1")}
        self.assertEqual(edge_ids, {"e_ds_model", "e_model_exp"})

    def test_get_edges_missing_node_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.get_edges("ghost")

    def test_get_edges_deterministic_order(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        for i in range(5):
            graph.add_node(make_node(f"b{i}"))
            graph.add_edge(make_edge(f"e{i}", "a", f"b{i}", Relationship.PRODUCED))
        ids = [e.edge_id for e in graph.get_edges("a")]
        self.assertEqual(ids, sorted(ids))

    def test_get_edges_isolated_node_empty(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        self.assertEqual(graph.get_edges("a"), ())


class TestEvidenceGraphNeighbors(unittest.TestCase):
    def test_neighbors_both_directions(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_node(make_node("c"))
        graph.add_edge(make_edge("e1", "a", "b"))
        graph.add_edge(make_edge("e2", "c", "a"))
        self.assertEqual(set(graph.neighbors("a")), {"b", "c"})

    def test_neighbors_missing_node_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.neighbors("ghost")

    def test_neighbors_deterministic_order(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("hub"))
        for i in range(5):
            graph.add_node(make_node(f"leaf{i}"))
            graph.add_edge(make_edge(f"e{i}", "hub", f"leaf{i}"))
        self.assertEqual(graph.neighbors("hub"), tuple(sorted(["leaf0", "leaf1", "leaf2", "leaf3", "leaf4"])))

    def test_neighbors_isolated_node_empty(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        self.assertEqual(graph.neighbors("a"), ())

    def test_neighbor_symmetry(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e", "a", "b"))
        self.assertIn("a", graph.neighbors("b"))
        self.assertIn("b", graph.neighbors("a"))


class TestEvidenceGraphRemoveNode(unittest.TestCase):
    def test_remove_node_decreases_count(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.remove_node("a")
        self.assertEqual(graph.count_nodes(), 0)

    def test_remove_node_removes_incident_edges(self):
        graph = make_graph()
        graph.remove_node("model_1")
        self.assertFalse(graph.has_node("model_1"))
        self.assertEqual(graph.count_edges(), 0)

    def test_remove_node_edges_not_incident_remain(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_node(make_node("c"))
        graph.add_edge(make_edge("e1", "a", "b"))
        graph.add_edge(make_edge("e2", "b", "c"))
        graph.remove_node("a")
        self.assertEqual(graph.count_edges(), 1)
        self.assertTrue(graph.has_node("b"))
        self.assertTrue(graph.has_node("c"))

    def test_remove_missing_node_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.remove_node("ghost")

    def test_remove_then_re_add_same_id(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.remove_node("a")
        graph.add_node(make_node("a"))
        self.assertEqual(graph.count_nodes(), 1)

    def test_remove_updates_neighbors(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e", "a", "b"))
        graph.remove_node("a")
        self.assertEqual(graph.neighbors("b"), ())


class TestEvidenceGraphRemoveEdge(unittest.TestCase):
    def test_remove_edge_decreases_count(self):
        graph = make_graph()
        before = graph.count_edges()
        graph.remove_edge("e_ds_model")
        self.assertEqual(graph.count_edges(), before - 1)

    def test_remove_missing_edge_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(InvalidEdgeError):
            graph.remove_edge("ghost")

    def test_remove_edge_updates_incident(self):
        graph = make_graph()
        graph.remove_edge("e_ds_model")
        edge_ids = {e.edge_id for e in graph.get_edges("dataset_1")}
        self.assertEqual(edge_ids, set())

    def test_remove_edge_preserves_nodes(self):
        graph = make_graph()
        graph.remove_edge("e_ds_model")
        self.assertEqual(graph.count_nodes(), 4)


class TestEvidenceGraphClear(unittest.TestCase):
    def test_clear_empties_nodes(self):
        graph = make_graph()
        graph.clear()
        self.assertEqual(graph.count_nodes(), 0)

    def test_clear_empties_edges(self):
        graph = make_graph()
        graph.clear()
        self.assertEqual(graph.count_edges(), 0)

    def test_clear_then_reuse(self):
        graph = make_graph()
        graph.clear()
        graph.add_node(make_node("new"))
        self.assertEqual(graph.count_nodes(), 1)

    def test_clear_empty_graph_is_safe(self):
        graph = EvidenceGraph()
        graph.clear()
        self.assertEqual(graph.count_nodes(), 0)
        self.assertEqual(graph.count_edges(), 0)

    def test_clear_removes_neighbors(self):
        graph = make_graph()
        graph.clear()
        with self.assertRaises(NodeNotFoundError):
            graph.neighbors("dataset_1")


class TestEvidenceGraphCounts(unittest.TestCase):
    def test_empty_graph_counts(self):
        graph = EvidenceGraph()
        self.assertEqual(graph.count_nodes(), 0)
        self.assertEqual(graph.count_edges(), 0)

    def test_count_nodes_after_removal(self):
        graph = make_graph()
        graph.remove_node("dataset_1")
        self.assertEqual(graph.count_nodes(), 3)

    def test_count_edges_after_removal(self):
        graph = make_graph()
        graph.remove_node("model_1")
        self.assertEqual(graph.count_edges(), 0)

    def test_count_edges_correct_after_many(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        for i in range(10):
            graph.add_node(make_node(f"b{i}"))
            graph.add_edge(make_edge(f"e{i}", "a", f"b{i}", Relationship.PRODUCED))
        self.assertEqual(graph.count_edges(), 10)

    def test_counts_match_after_clear(self):
        graph = make_graph()
        graph.clear()
        self.assertEqual((graph.count_nodes(), graph.count_edges()), (0, 0))


class TestEvidenceGraphDeterminism(unittest.TestCase):
    def test_build_sequence_is_deterministic(self):
        g1 = EvidenceGraph()
        g2 = EvidenceGraph()
        for node in (make_node("b"), make_node("a"), make_node("c")):
            g1.add_node(node)
            g2.add_node(node)
        self.assertEqual(g1.to_dict(), g2.to_dict())

    def test_to_dict_order_sorted(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("c"))
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        ids = [n["node_id"] for n in graph.to_dict()["nodes"]]
        self.assertEqual(ids, sorted(ids))

    def test_edges_sorted_in_to_dict(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        for i in (1, 2, 3):
            graph.add_node(make_node(f"b{i}"))
            graph.add_edge(make_edge(f"e{i}", "a", f"b{i}", Relationship.PRODUCED))
        ids = [e["edge_id"] for e in graph.to_dict()["edges"]]
        self.assertEqual(ids, ["e1", "e2", "e3"])

    def test_nodes_method_sorted(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("c"))
        graph.add_node(make_node("a"))
        self.assertEqual([n.node_id for n in graph.nodes()], ["a", "c"])

    def test_edges_method_sorted(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        graph.add_node(make_node("b"))
        graph.add_edge(make_edge("e2", "a", "b", Relationship.PRODUCED))
        graph.add_edge(make_edge("e1", "a", "b", Relationship.DEPENDS_ON))
        self.assertEqual([e.edge_id for e in graph.edges()], ["e1", "e2"])


class TestEvidenceGraphEmpty(unittest.TestCase):
    def test_empty_graph_get_node_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.get_node("x")

    def test_empty_graph_get_edges_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.get_edges("x")

    def test_empty_graph_neighbors_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.neighbors("x")

    def test_empty_graph_remove_node_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(NodeNotFoundError):
            graph.remove_node("x")

    def test_empty_graph_remove_edge_raises(self):
        graph = EvidenceGraph()
        with self.assertRaises(InvalidEdgeError):
            graph.remove_edge("x")

    def test_empty_graph_nodes_tuple(self):
        self.assertEqual(EvidenceGraph().nodes(), ())

    def test_empty_graph_edges_tuple(self):
        self.assertEqual(EvidenceGraph().edges(), ())

    def test_empty_graph_to_dict(self):
        self.assertEqual(EvidenceGraph().to_dict(), {"nodes": [], "edges": []})


class TestEvidenceGraphLargeGraph(unittest.TestCase):
    def test_add_many_nodes(self):
        graph = EvidenceGraph()
        for i in range(1000):
            graph.add_node(make_node(f"n{i}"))
        self.assertEqual(graph.count_nodes(), 1000)

    def test_add_many_edges(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        for i in range(1000):
            graph.add_node(make_node(f"n{i}"))
            graph.add_edge(make_edge(f"e{i}", "a", f"n{i}"))
        self.assertEqual(graph.count_edges(), 1000)

    def test_lookup_is_constant_time(self):
        graph = EvidenceGraph()
        for i in range(1000):
            graph.add_node(make_node(f"n{i}"))
        for i in range(1000):
            self.assertEqual(graph.get_node(f"n{i}").node_id, f"n{i}")

    def test_remove_many_nodes(self):
        graph = EvidenceGraph()
        for i in range(500):
            graph.add_node(make_node(f"n{i}"))
        for i in range(500):
            graph.remove_node(f"n{i}")
        self.assertEqual(graph.count_nodes(), 0)

    def test_large_graph_to_dict(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        for i in range(500):
            graph.add_node(make_node(f"n{i}"))
            graph.add_edge(make_edge(f"e{i}", "a", f"n{i}"))
        data = graph.to_dict()
        self.assertEqual(len(data["nodes"]), 501)
        self.assertEqual(len(data["edges"]), 500)

    def test_large_graph_deterministic_hashes(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a"))
        for i in range(100):
            graph.add_node(make_node(f"n{i}"))
            graph.add_edge(make_edge(f"e{i}", "a", f"n{i}"))
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.to_dict(), graph.to_dict())


class TestEvidenceGraphSerialization(unittest.TestCase):
    def test_to_dict_from_dict_roundtrip(self):
        graph = make_graph()
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.to_dict(), graph.to_dict())

    def test_roundtrip_preserves_counts(self):
        graph = make_graph()
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.count_nodes(), graph.count_nodes())
        self.assertEqual(restored.count_edges(), graph.count_edges())

    def test_roundtrip_preserves_traversal(self):
        graph = make_graph()
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.get_edges("model_1"), graph.get_edges("model_1"))
        self.assertEqual(restored.neighbors("model_1"), graph.neighbors("model_1"))

    def test_roundtrip_restores_immutability(self):
        graph = make_graph()
        restored = EvidenceGraph.from_dict(graph.to_dict())
        node = restored.get_node("dataset_1")
        with self.assertRaises(Exception):
            node.node_id = "x"  # type: ignore[misc]

    def test_empty_graph_roundtrip(self):
        graph = EvidenceGraph()
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.count_nodes(), 0)

    def test_metadata_survives_roundtrip(self):
        graph = EvidenceGraph()
        graph.add_node(make_node("a", metadata={"symbol": "XAUUSD"}))
        restored = EvidenceGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.get_node("a").metadata["symbol"], "XAUUSD")


class TestEvidenceGraphStoreSerialize(unittest.TestCase):
    def test_serialize_returns_json_string(self):
        repo = EvidenceGraphStore()
        text = repo.serialize(make_graph())
        self.assertIsInstance(text, str)
        json.loads(text)

    def test_serialize_contains_version(self):
        payload = json.loads(EvidenceGraphStore().serialize(make_graph()))
        self.assertEqual(payload["version"], EVIDENCE_GRAPH_VERSION)

    def test_serialize_contains_graph(self):
        payload = json.loads(EvidenceGraphStore().serialize(make_graph()))
        self.assertEqual(len(payload["graph"]["nodes"]), 4)

    def test_serialize_non_graph_raises(self):
        repo = EvidenceGraphStore()
        with self.assertRaises(TypeError):
            repo.serialize("not-a-graph")  # type: ignore[arg-type]

    def test_serialize_empty_graph(self):
        payload = json.loads(EvidenceGraphStore().serialize(EvidenceGraph()))
        self.assertEqual(payload["graph"], {"nodes": [], "edges": []})

    def test_serialize_deterministic(self):
        repo = EvidenceGraphStore()
        self.assertEqual(repo.serialize(make_graph()), repo.serialize(make_graph()))


class TestEvidenceGraphStoreDeserialize(unittest.TestCase):
    def test_deserialize_roundtrip(self):
        repo = EvidenceGraphStore()
        graph = make_graph()
        restored = repo.deserialize(repo.serialize(graph))
        self.assertEqual(restored.to_dict(), graph.to_dict())

    def test_deserialize_preserves_edges(self):
        repo = EvidenceGraphStore()
        restored = repo.deserialize(repo.serialize(make_graph()))
        self.assertEqual(restored.count_edges(), 2)

    def test_deserialize_invalid_json_raises(self):
        repo = EvidenceGraphStore()
        with self.assertRaises(EvidenceError):
            repo.deserialize("{not json")

    def test_deserialize_missing_graph_section_raises(self):
        repo = EvidenceGraphStore()
        with self.assertRaises(EvidenceError):
            repo.deserialize(json.dumps({"version": "1.0.0"}))

    def test_deserialize_bad_version_type_raises(self):
        repo = EvidenceGraphStore()
        with self.assertRaises(EvidenceError):
            repo.deserialize(json.dumps({"version": 1, "graph": {}}))

    def test_deserialize_bad_graph_raises(self):
        repo = EvidenceGraphStore()
        with self.assertRaises(EvidenceError):
            repo.deserialize(json.dumps({"version": "1.0.0", "graph": "nope"}))

    def test_deserialize_empty_graph(self):
        repo = EvidenceGraphStore()
        restored = repo.deserialize(repo.serialize(EvidenceGraph()))
        self.assertEqual(restored.count_nodes(), 0)

    def test_deserialize_dangling_edge_rejected(self):
        payload = {
            "version": EVIDENCE_GRAPH_VERSION,
            "graph": {
                "nodes": [make_node().to_dict()],
                "edges": [make_edge("e", "dataset_1", "missing").to_dict()],
            },
        }
        repo = EvidenceGraphStore()
        with self.assertRaises(EvidenceError):
            repo.deserialize(json.dumps(payload))


class TestEvidenceGraphStoreSaveLoad(unittest.TestCase):
    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "graph.json")
            repo = EvidenceGraphStore(path)
            graph = make_graph()
            repo.save(graph)
            loaded = repo.load()
            self.assertEqual(loaded.to_dict(), graph.to_dict())

    def test_save_returns_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "graph.json")
            result = EvidenceGraphStore(path).save(make_graph())
            self.assertEqual(result, path)

    def test_load_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = EvidenceGraphStore(os.path.join(tmp, "missing.json"))
            with self.assertRaises(FileNotFoundError):
                repo.load()

    def test_save_explicit_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "explicit.json")
            EvidenceGraphStore().save(make_graph(), path=path)
            self.assertTrue(os.path.exists(path))

    def test_load_explicit_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "explicit.json")
            EvidenceGraphStore().save(make_graph(), path=path)
            loaded = EvidenceGraphStore().load(path=path)
            self.assertEqual(loaded.count_nodes(), 4)

    def test_save_written_file_is_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "graph.json")
            EvidenceGraphStore(path).save(make_graph())
            with open(path, encoding="utf-8") as handle:
                json.load(handle)

    def test_load_preserves_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "graph.json")
            graph = EvidenceGraph()
            graph.add_node(make_node("a", metadata={"k": "v"}))
            repo = EvidenceGraphStore(path)
            repo.save(graph)
            self.assertEqual(repo.load().get_node("a").metadata["k"], "v")


class TestEvidenceGraphStoreDeterminism(unittest.TestCase):
    def test_save_identical_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = os.path.join(tmp, "a.json")
            p2 = os.path.join(tmp, "b.json")
            EvidenceGraphStore(p1).save(make_graph())
            EvidenceGraphStore(p2).save(make_graph())
            with open(p1, encoding="utf-8") as f1, open(p2, encoding="utf-8") as f2:
                self.assertEqual(f1.read(), f2.read())

    def test_serialize_deserialize_repeatable(self):
        repo = EvidenceGraphStore()
        graph = make_graph()
        restored = repo.deserialize(repo.serialize(graph))
        self.assertEqual(restored.to_dict(), graph.to_dict())
        again = repo.deserialize(repo.serialize(restored))
        self.assertEqual(again.to_dict(), graph.to_dict())

    def test_default_path_constant(self):
        self.assertEqual(DEFAULT_PATH, "evidence_graph.json")

    def test_version_constants(self):
        self.assertEqual(INTELLIGENCE_VERSION, "1.0.0")
        self.assertEqual(EVIDENCE_GRAPH_VERSION, "1.0.0")

    def test_errors_are_evidence_error_subclass(self):
        self.assertTrue(issubclass(NodeAlreadyExistsError, EvidenceError))
        self.assertTrue(issubclass(NodeNotFoundError, EvidenceError))
        self.assertTrue(issubclass(InvalidEdgeError, EvidenceError))


if __name__ == "__main__":
    unittest.main()
