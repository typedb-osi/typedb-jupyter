#
# Copyright (C) 2023 Vaticle
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from abc import abstractmethod
from typing import List, Any


############
# Vertices #
############
class AnswerVertex:
    def __init__(self, vertex):
        self.vertex = vertex

    def __str__(self):
        return str(self.vertex)

    def __hash__(self):
        return self.vertex.__hash__()

    def __eq__(self, other):
        return self.vertex.__eq__(other.vertex)

    @classmethod
    @abstractmethod
    def shape(cls):
        return cls._SHAPE

    @classmethod
    @abstractmethod
    def colour(cls):
        return cls._COLOUR

    @abstractmethod
    def label(self):
        raise NotImplementedError("abstract")

    @classmethod
    def trim_iid(cls, iid):
        full_iid =  str(iid)
        thing_id = full_iid[4:]
        trimmed = thing_id.lstrip("0")
        if len(trimmed) < 2:
            return thing_id[-2:]
        else:
            return trimmed

class RelationVertex(AnswerVertex):
    _SHAPE = "d"
    _COLOUR = "yellow"
    def __init__(self, relation):
        super().__init__(relation)

    def label(self):
        trimmed_iid = self.__class__.trim_iid(self.vertex.get_iid())
        return "{}[{}]".format(self.vertex.get_type().get_label(), trimmed_iid)


class EntityVertex(AnswerVertex):
    _SHAPE = "s"
    _COLOUR = "pink"
    def __init__(self, entity):
        super().__init__(entity)

    def label(self):
        trimmed_iid = self.__class__.trim_iid(self.vertex.get_iid())
        return "{}[{}]".format(self.vertex.get_type().get_label(), trimmed_iid)


class AttributeVertex(AnswerVertex):
    _SHAPE = "o"
    _COLOUR = "green"

    def __init__(self, attribute):
        super().__init__(attribute)

    def label(self):
        return "{}:{}".format(self.vertex.get_type().get_label(), self.vertex.get_value())

#########
# Edges #
#########
class AnswerEdge:
    def __init__(self, lhs: AnswerVertex, rhs: AnswerVertex):
        self.lhs = lhs
        self.rhs = rhs

    @abstractmethod
    def label(self):
        raise NotImplementedError("abstract")

    def __str__(self):
        return "{}--[{}]-->{}".format(self.lhs, self.label(), self.rhs)

class HasEdge(AnswerEdge):
    def label(self):
        return "has"


class LinksEdge(AnswerEdge):
    def __init__(self, lhs: AnswerVertex, rhs: AnswerVertex, role):
        super().__init__(lhs, rhs)
        self.role = role

    def label(self):
        return self.role.get_label().split(":")[1]

##########
# Graphs #
##########
class IGraphVisualisationBuilder:

    @abstractmethod
    def __init__(self):
        raise NotImplementedError("abstract")

    def add_entity_vertex(self, vertex: EntityVertex):
        raise NotImplementedError("abstract")

    def add_relation_vertex(self, vertex: RelationVertex):
        raise NotImplementedError("abstract")

    def add_attribute_vertex(self, vertex: AttributeVertex):
        raise NotImplementedError("abstract")

    def add_has_edge(self, edge: HasEdge):
        raise NotImplementedError("abstract")

    def add_links_edge(self, edge: LinksEdge):
        raise NotImplementedError("abstract")

    def plot(self) -> "Any":
        raise NotImplementedError("abstract")

class AnswerGraph:
    def __init__(self, edges: List[AnswerEdge]):
        self.edges = edges

    def plot(self):
        self.plot_with_visualiser(PlottableGraphBuilder())

    def plot_with_visualiser(self, visualiser: IGraphVisualisationBuilder):
        for edge in self.edges:
            self._plot_vertex(visualiser, edge.lhs)
            self._plot_vertex(visualiser, edge.rhs)
            self._plot_edge(visualiser, edge)
        return visualiser.plot()

    def _plot_vertex(self, visualiser: IGraphVisualisationBuilder, vertex: AnswerVertex):
        if isinstance(vertex, EntityVertex):
            visualiser.add_entity_vertex(vertex)
        elif isinstance(vertex, RelationVertex):
            visualiser.add_relation_vertex(vertex)
        elif isinstance(vertex, AttributeVertex):
            visualiser.add_attribute_vertex(vertex)
        else:
            raise ValueError(f"Unknown vertex type: {vertex}")

    def _plot_edge(self, visualiser: IGraphVisualisationBuilder, edge: AnswerEdge):
        if isinstance(edge, HasEdge):
            visualiser.add_has_edge(edge)
        elif isinstance(edge, LinksEdge):
            visualiser.add_links_edge(edge)
        else:
            raise ValueError(f"Unknown edge type: {edge}")


class AnswerGraphBuilder:
    def __init__(self, query_graph):
        self.query_graph = query_graph
        self.edges = []

    @classmethod
    def build(cls, query_graph, answers):
        relevant_edges = cls._filter_visualisable_edges(query_graph)
        builder = AnswerGraphBuilder(query_graph)
        for row in answers:
            builder._add_answer_row(row)
        return AnswerGraph(builder.edges)

    @classmethod
    def _filter_visualisable_edges(cls, query_graph):
        query_graph # TODO

    def _add_answer_row(self, row):
        for query_edge in self.query_graph.edges:
            edge = query_edge.get_answer_edge(row)
            self.edges.append(edge)


class PlottableGraphBuilder(IGraphVisualisationBuilder):
    def __init__(self):
        self.edges = []
        self.edge_labels = {}
        self.node_shapes = {}
        self.node_colours = {}
        self.node_labels= {}

    def _add_edge_defaults(self, edge: AnswerEdge):
        self.edges.append((edge.lhs, edge.rhs))
        self.edge_labels[(edge.lhs, edge.rhs)] = edge.label()

    def _add_vertex_defaults(self, vertex: AnswerVertex):
        self.node_shapes[vertex] = vertex.shape()
        self.node_colours[vertex] = vertex.colour()
        self.node_labels[vertex] = vertex.label()


    def add_entity_vertex(self, vertex: EntityVertex):
        self._add_vertex_defaults(vertex)

    def add_relation_vertex(self, vertex: RelationVertex):
        self._add_vertex_defaults(vertex)

    def add_attribute_vertex(self, vertex: AttributeVertex):
        self._add_vertex_defaults(vertex)

    def add_has_edge(self, edge: HasEdge):
        self._add_edge_defaults(edge)

    def add_links_edge(self, edge: LinksEdge):
        self._add_edge_defaults(edge)

    def plot(self):
        from netgraph import InteractiveGraph
        return InteractiveGraph(
            self.edges,
            edge_labels=self.edge_labels,
            node_shape=self.node_shapes,
            node_color=self.node_colours,
            node_labels=self.node_labels,
            arrows=True,
            node_label_offset=0.075
        )

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from netgraph import InteractiveGraph
    graph_data = [("a", "b"), ("b", "c")]
    node_shapes = { "a" : "o", "b" : "s", "c": "o"}
    plot_instance = InteractiveGraph(graph_data, node_shape=node_shapes)
    plt.show()
