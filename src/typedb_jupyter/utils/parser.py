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


from parsimonious.grammar import Grammar
from parsimonious.nodes import Node, NodeVisitor

from ir import Var, Label, Literal, Comparator, \
    Isa, Has, Links, IsaType, AttributeLabelValue, Comparison, Assign

class Match:
    def __init__(self, constraints):
        self.constraints = constraints


    def __str__(self):
        return "Match(%s)"%(", ".join(str(c) for c in self.constraints))


def flatten(l):
    flat = []
    for sl in l:
        if isinstance(sl, list):
            flat = flat + flatten(sl)
        else:
            flat.append(sl)
    return flat


def non_null(l):
    return [e for e in l if e is not None]

class TypeQLVisitor(NodeVisitor):
    GRAMMAR = Grammar("""
        query  = ws match_clause ws
    
        match_clause = "match" ws (pattern ";" ws)+
                      
        pattern =  native / assign / comparison
        assign = "TODO"
        
        comparison = (var/literal) ws comparator ws (var/literal) ws
        comparator = "=" / ">" / ">=" / "<" / "<=" / "!=" / "like" / "contains"
        
        native = var ws constraint ws ( "," ws constraint ws)* 
        constraint = has_labelled / has / links / isa 
    
        has_labelled = "has" ws label ws (var / literal)    
        has = "has" ws var
    
        links = "links" ws "(" ws role_player ws ( "," ws constraint ws)* ")"
        isa = "isa" ws (label/var)
        
        role_player = (var/label) ws ":" ws var
        
        label = ~"[A-Za-z0-9_\-]+"
        identifier = ~"[A-Za-z0-9_\-]+"
        var =  ~"\$[A-Za-z0-9_\-]+"
        literal = (integer_literal / string_literal)
        integer_literal = ~"[0-9]+"
        string_literal = ~'"[^\"]+"'
        ignored = ~"[^']+"
        ws = ~"\s*"
    """)

    def visit_ws(self, node:Node, visited_children):
        return

    def visit_var(self, node:Node, visited_children):
        return Var(node.text)

    def visit_label(self, node:Node, visited_children):
        return Label(node.text)

    def visit_identifier(self, node:Node, visited_children):
        return node.text

    def visit_literal(self, node:Node, visited_children):
        return Literal(node.text)

    def visit_query(self, node:Node, visited_children):
        parts = tuple(v for v in flatten(visited_children))
        # assert len(parts) == 2
        return parts

    def visit_match_clause(self, node:Node, visited_children):
        return Match(non_null(flatten(visited_children)))


    def visit_pattern(self, node:Node, visited_children):
        return flatten(non_null(visited_children)) # TODO: Try removing non_null

    def visit_assign(self, node: Node, visited_children):
        return non_null(visited_children)[0]

    def visit_native(self, node:Node, visited_children):
        children = non_null(flatten(visited_children))
        edges = []
        u = children[0]
        # print("U was ", u)
        for constraint in children[1:]:
            constraint.may_set_lhs(u)
            # print("Child is", child)
            edges.append(constraint)
        return edges

    def visit_constraint(self, node: Node, visited_children):
        assert len(visited_children) == 1
        return visited_children[0]

    def visit_has_labelled(self, node: Node, visited_children):
        [label, rhs] = non_null(flatten(visited_children))
        if isinstance(rhs, Var):
            attr_var = rhs
            return [Has(None, attr_var), IsaType(attr_var, label)]
        else:
            assert isinstance(rhs, Literal)
            attr_var = Var.next_internal()
            return [Has(None, attr_var), AttributeLabelValue(attr_var, label, rhs)]

    def visit_links(self, node: Node, visited_children):
        return non_null(visited_children)

    def visit_role_player(self, node: Node, visited_children):
        [role, player] = non_null(flatten(visited_children))
        print((role, player))
        if isinstance(role, Var):
            return [Links(None, player, role)]
        else:
            assert isinstance(role, Label)
            return [Links(None, player, role)]

    def visit_has(self, node: Node, visited_children):
        return [Has(None, visited_children[0])]

    def visit_isa(self, node: Node, visited_children):
        [label_or_var] = non_null(flatten(visited_children))
        if isinstance(label_or_var, Label):
            return [IsaType(None, label_or_var)]
        else:
            assert isinstance(label_or_var, Var)
            return [Isa(None, label_or_var)]

    def visit_comparison(self, node: Node, visited_children):
        [lhs, comparator, rhs] = non_null(flatten(visited_children))
        return [Comparison(lhs, rhs, comparator)]

    def visit_comparator(self, node: Node, visited_children):
        return [Comparator(node.text)]

    def generic_visit(self, node:Node, visited_children):
        """ The generic visit method. """
        # print("Generic visit for ", node)
        return visited_children or None

if __name__ == "__main__":
    input = """
    match
    $x isa cow, has name "Spider Georg";
    $y isa cow, has name "Spider Georg";
    $z isa marriage, links (man: $x);
    """

    tree = TypeQLVisitor.GRAMMAR.parse(input)
    # print(tree)
    # print("=====")
    visitor = TypeQLVisitor()
    visited = visitor.visit(tree)
    print("\n----\n".join((str(v) for v in visited )))
