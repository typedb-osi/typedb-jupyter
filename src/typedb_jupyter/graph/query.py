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

from ir import Var, Label, Literal, Comparator, \
    Isa, Has, Links, IsaType, AttributeLabelValue, Comparison, Assign
from abc import abstractmethod


class QueryGraphEdge:
    def __init__(self, left:Var, right:Var):
        self.left = left
        self.right = right

    @abstractmethod
    def label(self):
        raise NotImplementedError("abstract")

    @abstractmethod
    def left_shape(self):
        raise NotImplementedError("abstract")

    @abstractmethod
    def right_shape(self):
        raise NotImplementedError("abstract")


    def get_answer_edges(self, row):
        return ()

class QueryHasEdge(QueryGraphEdge):
    def label(self):
        return "has"

    def shape(self):

def lazy_query_graph(constraints):
    graph = []
    for c in constraints:
        if isinstance(c, Has):
            graph.append(QueryGraphEdge(c.lhs, "has", c.rhs))
        elif isinstance(c, Links):
            graph.append(QueryGraphEdge(c.lhs, c.role, c.rhs))
    return graph

