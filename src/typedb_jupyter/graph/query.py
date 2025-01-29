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

from typedb_jupyter.utils.ir import Var, Label, Literal, Comparator, \
    Isa, Has, Links, IsaType, AttributeLabelValue, Comparison, Assign
from typedb_jupyter.graph.answer import HasEdge, LinksEdge

class QueryGraphEdge:
    def __init__(self, lhs: Var, rhs: Var):
        self.lhs = lhs
        self.rhs = rhs


    @abstractmethod
    def get_answer_edge(self, row):
        raise NotImplementedError("abstract")

    @abstractmethod
    def __str__(self):
        raise NotImplementedError("abstract")

class QueryHasEdge(QueryGraphEdge):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs)

    def get_answer_edge(self, row):
        return HasEdge(row.get(self.lhs.name), row.get(self.rhs.name))

    def __str__(self):
        return "{}({}, {})".format(self.__class__.__name__, self.lhs, self.rhs)


class QueryLinksEdge(QueryGraphEdge):
    def __init__(self, lhs, rhs, role):
        super().__init__(lhs, rhs)
        self.role = role

    def get_answer_edge(self, row):
        return LinksEdge(row.get(self.lhs), row.get(self.rhs), row.get(self.role))

    def __str__(self):
        return "{}({}, {}, {})".format(self.__class__.__name__, self.lhs, self.rhs, self.role)

class QueryGraph:
    def __init__(self, query: "typedb_jupyter.utils.ir.Match"):
        self.edges = lazy_query_graph(query.constraints)



def lazy_query_graph(constraints):
    edges = []
    for c in constraints:
        if isinstance(c, Has):
            edges.append(QueryHasEdge(c.lhs, c.rhs))
        elif isinstance(c, Links):
            edges.append(QueryLinksEdge(c.lhs, c.rhs, c.role))
    return edges

