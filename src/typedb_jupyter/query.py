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

import math
from typedb.client import TypeDBOptions
from typedb.api.connection.session import SessionType
from typedb.api.connection.transaction import TransactionType
from typedb.concept.answer.concept_map import ConceptMap
from typedb.concept.answer.concept_map_group import ConceptMapGroup
from typedb.concept.answer.numeric import Numeric
from typedb.concept.answer.numeric_group import NumericGroup
from typedb_jupyter.connection import Connection
from typedb_jupyter.exception import ArgumentError, QueryParsingError


class Query(object):
    def __init__(self, query, session_arg, transaction_arg, inference_arg, strict_transactions, global_inference):
        self.query = query
        self.query_type = self._get_query_type(self.query)
        self.session_type = self._get_session_type(self.query_type, session_arg, strict_transactions)
        self.transaction_type = self._get_transaction_type(self.query_type, transaction_arg, strict_transactions)

        if inference_arg is None:
            self.infer = global_inference
        else:
            self.infer = inference_arg

    @staticmethod
    def _get_query_args(query):
        # Warning: This method is experimental and not guaranteed to always function correctly. Copy at your own risk.

        in_escape = False
        in_literal = False
        in_comment = False
        literal_delimiter = None
        arg_string = ""

        for char in query:
            if in_escape:
                in_escape = False
                arg_string += " "
                continue

            if in_literal and char == "\\":
                in_escape = True
                arg_string += " "
                continue

            if not in_comment and char in ("\"", "'"):
                if not in_literal:
                    in_literal = True
                    literal_delimiter = char
                    arg_string += " "
                    continue
                if in_literal and char == literal_delimiter:
                    in_literal = False
                    arg_string += " "
                    continue

            if not in_literal:
                if char == "#":
                    in_comment = True
                    arg_string += " "
                    continue
                if in_comment and char == "\n":
                    in_comment = False
                    arg_string += " "
                    continue

            if not in_literal and not in_comment:
                arg_string += char

        return arg_string.replace(",", " ").replace(";", " ").split()

    @staticmethod
    def _get_query_type(query):
        # Warning: This method is experimental and not guaranteed to always function correctly. Copy at your own risk.

        query_args = Query._get_query_args(query)

        keyword_counts = {
            "match": 0,
            "get": 0,
            "define": 0,
            "undefine": 0,
            "insert": 0,
            "delete": 0,
            "group": 0,
            "count": 0,
            "sum": 0,
            "max": 0,
            "min": 0,
            "mean": 0,
            "median": 0,
            "std": 0,
        }

        for arg in query_args:
            if arg in keyword_counts:
                keyword_counts[arg] += 1

        aggregate_count = sum((
            keyword_counts["count"],
            keyword_counts["sum"],
            keyword_counts["max"],
            keyword_counts["min"],
            keyword_counts["mean"],
            keyword_counts["median"],
            keyword_counts["std"],
        ))

        candidate_query_types = list()

        if keyword_counts["group"] > 0 and aggregate_count > 0:
            candidate_query_types.append("match-group-aggregate")
        elif aggregate_count > 0:
            candidate_query_types.append("match-aggregate")
        elif keyword_counts["group"] > 0:
            candidate_query_types.append("match-group")
        elif keyword_counts["get"] > 0:
            candidate_query_types.append("match")

        if keyword_counts["define"] > 0:
            candidate_query_types.append("define")

        if keyword_counts["undefine"] > 0:
            candidate_query_types.append("undefine")

        if keyword_counts["insert"] > 0 and keyword_counts["delete"] > 0:
            candidate_query_types.append("update")
        elif keyword_counts["insert"] > 0:
            candidate_query_types.append("insert")
        elif keyword_counts["delete"] > 0:
            candidate_query_types.append("delete")

        if len(candidate_query_types) > 1:
            raise QueryParsingError("Query contains incompatible keywords: '{}'".format("', '".join(candidate_query_types)))
        elif len(candidate_query_types) == 1:
            return candidate_query_types[0]
        elif keyword_counts["match"] > 0:
            return "match"
        else:
            raise QueryParsingError("Query contains no keywords.")

    @staticmethod
    def _get_session_type(query_type, session_arg, strict_transactions):
        if session_arg is None:
            if strict_transactions:
                raise ArgumentError("Strict transaction types is enabled and no session type was provided. Use -s to specify session type.")
            elif query_type in ("define", "undefine"):
                return SessionType.SCHEMA
            else:
                return SessionType.DATA
        else:
            if session_arg.lower() == "schema":
                return SessionType.SCHEMA
            elif session_arg.lower() == "data":
                return SessionType.DATA
            else:
                raise ArgumentError("Incorrect session type provided. Session type must be 'schema' or 'data'.")

    @staticmethod
    def _get_transaction_type(query_type, transaction_arg, strict_transactions):
        if transaction_arg is None:
            if strict_transactions:
                raise ArgumentError("Strict transaction types is enabled and no transaction type was provided. Use -t to specify transaction type.")
            elif query_type in ("define", "undefine", "insert", "update", "delete"):
                return TransactionType.WRITE
            else:
                return TransactionType.READ
        else:
            if transaction_arg.lower() == "read":
                return TransactionType.READ
            elif transaction_arg.lower() == "write":
                return TransactionType.WRITE
            else:
                raise ArgumentError("Incorrect transaction type provided. Transaction type must be 'read' or 'write'.")

    def _get_options(self, connection):
        if connection.client.is_cluster():
            return TypeDBOptions().cluster().set_infer(self.infer)
        else:
            return TypeDBOptions().core().set_infer(self.infer)

    def _print_info(self, connection):
        connection_arg = "Connection: {}".format(connection.verbose_name)

        if self.session_type == SessionType.SCHEMA:
            session_arg = "Session: schema"
        else:
            session_arg = "Session: data"

        if self.transaction_type == TransactionType.READ:
            transaction_arg = "Transaction: read"
        else:
            transaction_arg = "Transaction: write"

        query_arg = "Query: {}".format(self.query_type)

        if self.infer:
            inference_arg = "Inference: on"
        else:
            inference_arg = "Inference: off"

        info = "{}\n{}\n{}\n{}\n{}".format(
            connection_arg, session_arg, transaction_arg, query_arg, inference_arg
        )

        print(info)

    @staticmethod
    def _group_key(concept):
        if concept.is_type():
            return str(concept.as_type().get_label())
        elif concept.is_entity():
            return concept.as_entity().get_iid()
        elif concept.is_relation():
            return concept.as_relation().get_iid()
        elif concept.is_attribute():
            return concept.as_attribute().get_value()
        else:
            raise ValueError("Unknown concept type. Please report this error.")

    @staticmethod
    def _parse_answer(answer, answer_type):
        if answer_type is ConceptMap:
            return [concept_map.to_json() for concept_map in answer]
        elif answer_type is ConceptMapGroup:
            return {Query._group_key(map_group.owner()): Query._parse_answer(map_group.concept_maps(), ConceptMap) for map_group in answer}
        elif answer_type is Numeric:
            if answer.is_int():
                return answer.as_int()
            elif answer.is_float():
                return answer.as_float()
            else:
                return math.nan
        elif answer_type is NumericGroup:
            return {Query._group_key(numeric_group.owner()): Query._parse_answer(numeric_group.numeric(), Numeric) for numeric_group in answer}
        else:
            raise ValueError("Unknown answer type. Please report this error.")

    def run(self, connection, show_info):
        Connection.set_session(self.session_type)
        options = self._get_options(connection)

        if show_info:
            self._print_info(connection)

        try:
            with connection.session.transaction(self.transaction_type, options) as transaction:
                if self.query_type == "match":
                    results = self._parse_answer(transaction.query().match(self.query), ConceptMap)
                elif self.query_type == "match-aggregate":
                    results = self._parse_answer(transaction.query().match_aggregate(self.query).get(), Numeric)
                elif self.query_type == "match-group":
                    results = self._parse_answer(transaction.query().match_group(self.query), ConceptMapGroup)
                elif self.query_type == "match-group-aggregate":
                    results = self._parse_answer(transaction.query().match_group_aggregate(self.query), NumericGroup)
                elif self.query_type == "define":
                    transaction.query().define(self.query)
                elif self.query_type == "undefine":
                    transaction.query().undefine(self.query)
                elif self.query_type == "insert":
                    transaction.query().insert(self.query)
                elif self.query_type == "delete":
                    transaction.query().delete(self.query)
                elif self.query_type == "update":
                    transaction.query().update(self.query)

                if self.transaction_type == TransactionType.WRITE:
                    transaction.commit()
                    print('{} query success.'.format(self.query_type.title()))
                    return
                else:
                    return results
        finally:
            Connection.set_session(SessionType.DATA)
