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

class AnswerGraph:
    def __init__(self, edges):
        self.edges = edges

    def draw(self):
        from netgraph import Graph
        # TODO: derive edges, node_shape, node_labels, node_colors from  from edge.lhs & edge.rhs
        plottable = PlottableGraphBuilder()
        for edge in self.edges:
            plottable.add_edge(edge)
        plot_instance = Graph(
            plottable.edges,
            edge_labels=plottable.edge_labels,
            node_shape=plottable.node_shapes,
            node_color=plottable.node_colours,
            node_labels=plottable.node_labels,
            arrows=True,
            node_label_offset=0.075
        )

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

class RelationVertex(AnswerVertex):
    _SHAPE = "o"
    _COLOUR = "green"
    def __init__(self, relation):
        super().__init__(relation)

    def label(self):
        return str(self)


class EntityVertex(AnswerVertex):
    _SHAPE = "o"
    _COLOUR = "green"
    def __init__(self, entity):
        super().__init__(entity)

    def label(self):
        return str(self)


class AttributeVertex(AnswerVertex):
    _SHAPE = "s"
    _COLOUR = "green"

    def __init__(self, attribute):
        super().__init__(attribute)

    def label(self):
        return str(self)

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
    def __init__(self, lhs: AnswerVertex, rhs: AnswerVertex, role: AnswerVertex):
        super().__init__(lhs, rhs)
        self.role = role

    def label(self):
        return str(self.role) # TODO


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


class PlottableGraphBuilder:
    def __init__(self):
        self.edges = []
        self.edge_labels = {}
        self.node_shapes = {}
        self.node_colours = {}
        self.node_labels= {}

    def add_edge(self, edge: AnswerEdge):
        self.edges.append((edge.lhs, edge.rhs))
        self.edge_labels[(edge.lhs, edge.rhs)] = edge.label()
        self.node_shapes[edge.lhs] = edge.lhs.shape()
        self.node_shapes[edge.rhs] = edge.rhs.shape()

        self.node_colours[edge.lhs] = edge.lhs.colour()
        self.node_colours[edge.rhs] = edge.rhs.colour()

        self.node_labels[edge.lhs] = edge.lhs.label()
        self.node_labels[edge.rhs] = edge.rhs.label()



if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from netgraph import Graph, InteractiveGraph, EditableGraph
    graph_data = [("a", "b"), ("b", "c")]
    # Graph(graph_data)
    # plt.show()
    node_shapes = { "a" : "o", "b" : "s", "c": "o"}
    plot_instance = InteractiveGraph(graph_data, node_shape=node_shapes)
    plt.show()
