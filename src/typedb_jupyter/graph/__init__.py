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

def visualise(typeql_query_string, typeql_result, visualiser=None):
    from typedb_jupyter.graph.query import QueryGraph
    from typedb_jupyter.graph.answer import AnswerGraph
    from typedb_jupyter.utils.parser import TypeQLVisitor

    parsed = TypeQLVisitor.parse_and_visit(typeql_query_string)
    query_graph = QueryGraph(parsed)
    answer_graph = AnswerGraph.build(query_graph, typeql_result)
    if visualiser is None:
        from .answer import PlottableGraphBuilder
        visualiser = PlottableGraphBuilder()
    answer_graph.plot_with_visualiser(visualiser)