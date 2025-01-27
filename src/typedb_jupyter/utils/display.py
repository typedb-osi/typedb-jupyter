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

def print_rows(rows):
    if len(rows) == 0:
        print("Query returned an empty set of rows.")
    else:
        from IPython.display import HTML, display
        print("Query returned {} rows.".format(len(rows)))
        headers = list(rows[0].column_names())
        display(HTML(
            '<table><tr><th>{}</th></tr><tr>{}</tr></table>'.format(
                '</th><th>'.join(str(_) for _ in headers),
                '</tr><tr>'.join(
                    '<td>{}</td>'.format('</td><td>'.join(str(_) for _ in row.concepts())) for row in rows)
            )
        ))

def print_documents(documents):
    if len(documents) == 0:
        print("Query returned an empty set of documents.")
    else:
        from json import dumps
        print("Query returned {} documents.".format(len(documents)))
        for document in documents:
            print(dumps(document, indent=2))

def display_graph(graph):
    for edge in graph:
        