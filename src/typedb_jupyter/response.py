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
from typedb.concept.answer.concept_map import ConceptMap
from typedb.concept.answer.concept_map_group import ConceptMapGroup
from typedb.concept.answer.numeric import Numeric
from typedb.concept.answer.numeric_group import NumericGroup
from typedb_jupyter.exception import ArgumentError


class Response(object):
    def __init__(self, query, answer, output_format, transaction):
        self.query = query
        self.output_format = output_format
        self.answer_type = self._get_answer_type()
        self.result, self.message = self._format(self.query, answer, self.answer_type, output_format, transaction)

    def _get_answer_type(self):
        if self.query.query_type == "match":
            return ConceptMap
        elif self.query.query_type == "match-aggregate":
            return Numeric
        elif self.query.query_type == "match-group":
            return ConceptMapGroup
        elif self.query.query_type == "match-group-aggregate":
            return NumericGroup
        elif self.query.query_type == "define":
            return None
        elif self.query.query_type == "undefine":
            return None
        elif self.query.query_type == "insert":
            return None
        elif self.query.query_type == "delete":
            return None
        elif self.query.query_type == "update":
            return None

    @staticmethod
    def _group_key(concept):
        if concept.is_type():
            return concept.as_type().get_label().name()
        elif concept.is_entity():
            return concept.as_entity().get_iid()
        elif concept.is_relation():
            return concept.as_relation().get_iid()
        elif concept.is_attribute():
            return concept.as_attribute().get_value()
        else:
            raise ValueError("Unknown concept type. Please report this error.")

    @staticmethod
    def _format_json(answer, answer_type):
        if answer_type is ConceptMap:
            return [concept_map.to_json() for concept_map in answer]
        elif answer_type is ConceptMapGroup:
            return {Response._group_key(map_group.owner()): Response._format_json(map_group.concept_maps(), ConceptMap) for map_group in answer}
        elif answer_type is Numeric:
            if answer.is_int():
                return answer.as_int()
            elif answer.is_float():
                return answer.as_float()
            else:
                return math.nan
        elif answer_type is NumericGroup:
            return {Response._group_key(numeric_group.owner()): Response._format_json(numeric_group.numeric(), Numeric) for numeric_group in answer}
        else:
            raise ValueError("Unknown answer type. Please report this error.")

    @staticmethod
    def _serialise_concepts(results, transaction):
        concepts = dict()
        binding_counts = dict()

        for result in results:
            concept_map = result.map()

            for binding in concept_map.keys():
                if not concept_map[binding].is_thing():
                    continue

                thing = concept_map[binding].as_thing()
                iid = thing.get_iid()

                if iid not in concepts.keys():
                    if binding not in binding_counts.keys():
                        binding_counts[binding] = 1
                    else:
                        binding_counts[binding] += 1

                    concept = {
                        "binding": "{}_{}".format(binding, binding_counts[binding]),
                        "object": thing,
                    }

                    concepts[iid] = concept

        for concept in concepts.values():
            concept["type"] = concept["object"].get_type().get_label().name()

            if concept["object"].is_attribute():
                concept["root-type"] = transaction.concepts().get_root_attribute_type().get_label().name()
                concept["value"] = concept["object"].as_attribute().get_value()
                concept["value-type"] = str(concept["object"].get_type().get_value_type())

            if concept["object"].is_entity():
                concept["root-type"] = transaction.concepts().get_root_entity_type().get_label().name()
                ownerships = [attribute.get_iid() for attribute in concept["object"].as_remote(transaction).get_has()]
                concept["ownerships"] = [concepts[iid]["binding"] for iid in ownerships if iid in concepts.keys()]

            if concept["object"].is_relation():
                concept["root-type"] = transaction.concepts().get_root_relation_type().get_label().name()
                ownerships = [attribute.get_iid() for attribute in concept["object"].as_remote(transaction).get_has()]
                concept["ownerships"] = [concepts[iid]["binding"] for iid in ownerships if iid in concepts.keys()]
                roleplayers = concept["object"].as_remote(transaction).get_players_by_role_type()
                concept["roleplayers"] = list()

                for role in roleplayers.keys():
                    for roleplayer in roleplayers[role]:
                        iid = roleplayer.get_iid()

                        if iid in concepts.keys():
                            concept["roleplayers"].append((role.get_label().name(), concepts[iid]["binding"]))

            concept.pop("object")

        serial = {concept["binding"]: concept for concept in concepts.values()}

        for entry in serial.values():
            entry.pop("binding")

        return serial

    @staticmethod
    def _format_typeql(answer, answer_type, transaction):
        if answer_type is ConceptMap:
            concepts = Response._serialise_concepts(answer, transaction)
            lines = list()

            for binding, concept in concepts.items():
                lines.append("${} isa {};".format(binding, concept["type"]))

                if "value" in concept.keys():
                    if concept["value-type"] == "string":
                        lines.append("${} \"{}\";".format(binding, concept["value"]))
                    else:
                        lines.append("${} {};".format(binding, concept["value"]))

                if "ownerships" in concept.keys():
                    for attribute_binding in concept["ownerships"]:
                        lines.append("${} has ${};".format(binding, attribute_binding))

                if "roleplayers" in concept.keys():
                    if len(concept["roleplayers"]) > 0:
                        roleplayers = list()

                        for roleplayer in concept["roleplayers"]:
                            roleplayers.append("{}: ${}".format(roleplayer[0], roleplayer[1]))

                        lines.append("${} ({});".format(binding, ", ".join(roleplayers)))

            return "\n".join(lines)
        elif answer_type in (ConceptMapGroup, Numeric, NumericGroup):
            raise ArgumentError("TypeQL output is not possible for group and aggregate queries.")
        else:
            raise ValueError("Unknown answer type. Please report this error.")

    @staticmethod
    def _format(query, answer, answer_type, output_format, transaction):
        if answer_type is None:
            result = None
            message = "{} query success.".format(query.query_type.title())
            return result, message
        else:
            if output_format == "json":
                result = Response._format_json(answer, answer_type)
                message = None
            elif output_format == "typeql":
                result = Response._format_typeql(answer, answer_type, transaction)
                message = None
            else:
                raise ArgumentError("Unknown output format: '{}'".format(output_format))

            return result, message
