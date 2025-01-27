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

class AnswerVertex:

    @classmethod
    @abstractmethod
    def shape(cls):
        return cls._SHAPE

    @classmethod
    @abstractmethod
    def color(cls):
        return cls._COLOR

    @abstractmethod
    def label(self):
        raise NotImplementedError("abstract")

class RelationVertex(AnswerVertex):
    _SHAPE = "o"
    def __init__(self, relation):
        self.relation = relation

    def label(self):
        return "TODO_RELATION"


class EntityVertex(AnswerVertex):
    def __init__(self, entity):
        self.entity = entity

    def label(self):
        return "TODO_ENTITY"


class AttributeVertex(AnswerVertex):
    def __init__(self, attribute):
        self.attribute = attribute

    def label(self):
        return "TODO_ATTRIBUTE"

class AnswerEdge:
    def __init__(self, left: AnswerVertex, right: AnswerVertex):
        self.left = left
        self.right = right

    @abstractmethod
    def label(self):
        raise NotImplementedError("abstract")

class HasEdge(AnswerEdge):
    def label(self):
        return "has"


class LinksEdge(AnswerEdge):
    def __init__(self, left: AnswerVertex, right: AnswerVertex, role):
        super().__init__(left, right)
        self.role = role
    def label(self):
        return str(self.role) # TODO

class AnswerGraphBuilder:
    def __init__(self, query_graph):
        self.edges = []
        self.query_graph = AnswerGraphBuilder._filter_visualisable_edges(query_graph)
        self.answer_edges = []
        self.edge_labels = []

    @classmethod
    def _filter_visualisable_edges(cls, query_graph):
        query_graph # TODO

    def add_answer_row(self, row):
        for query_edge in self.query_graph:
            edge = query_edge.get_answer_edges(row)
            self.answer_edges.append((edge.left, edge.right))
            self.edge_labels.append(edge.label)

    def draw(self):
        from netgraph import InteractiveGraph
        # TODO: derive node_shape, node_labels, node_colors from  from edge.left & edge.right
        plot_instance = InteractiveGraph(self.answer_edges)
        plt.show()


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from netgraph import Graph, InteractiveGraph, EditableGraph
    graph_data = [("a", "b"), ("b", "c")]
    # Graph(graph_data)
    # plt.show()
    node_shapes = { "a" : "o", "b" : "s", "c": "o"}
    plot_instance = InteractiveGraph(graph_data, node_shape=node_shapes)
    plt.show()
