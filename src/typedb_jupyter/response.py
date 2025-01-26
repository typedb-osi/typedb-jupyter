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

from typedb.concept.answer.concept_row_iterator import ConceptRowIterator
from typedb.concept.answer.concept_document_iterator import ConceptDocumentIterator
from typedb.concept.answer.ok_query_answer import OkQueryAnswer
from typedb_jupyter.exception import ArgumentError

raise NotImplementedError("Do not import me")

# class Response(object):
#     def __init__(self, query, answer, output_format, transaction):
#         self.query = query
#         self.output_format = output_format
#         self.answer_type = self._get_answer_type(answer)
#         self.result, self.message = self._format(self.query, answer, self.answer_type, output_format, transaction)
#
#     @staticmethod
#     def _get_answer_type(answer):
#         if answer.is_concept_rows():
#             return ConceptRowIterator
#         elif answer.is_concept_documents():
#             return ConceptDocumentIterator
#         elif answer.is_ok():
#             return OkQueryAnswer
#         else:
#             raise NotImplementedError("Unhandled answer type")
#
#     @staticmethod
#     def _group_key(concept):
#         if concept.is_type():
#             return concept.as_type().get_label().name
#         elif concept.is_entity():
#             return concept.as_entity().get_iid()
#         elif concept.is_relation():
#             return concept.as_relation().get_iid()
#         elif concept.is_attribute():
#             return concept.as_attribute().get_value()
#         else:
#             raise ValueError("Unknown concept type. Please report this error.")
#
#     @staticmethod
#     def _format_json(answer, answer_type):
#         if answer_type is ConceptRowIterator:
#             return [str(concept_row) for concept_row in answer]
#         else:
#             raise ValueError("Unknown answer type. Please report this error.")
#
#     @staticmethod
#     def _serialise_concepts(results, transaction):
#         concepts = dict()
#         binding_counts = dict()
#
#         for result in results:
#             concept_map = result.map
#
#             for binding in concept_map.keys():
#                 if not concept_map[binding].is_thing():
#                     continue
#
#                 thing = concept_map[binding].as_thing()
#                 iid = thing.get_iid()
#
#                 if iid not in concepts.keys():
#                     if binding not in binding_counts.keys():
#                         binding_counts[binding] = 1
#                     else:
#                         binding_counts[binding] += 1
#
#                     concept = {
#                         "binding": "{}_{}".format(binding, binding_counts[binding]),
#                         "object": thing,
#                     }
#
#                     concepts[iid] = concept
#
#         for concept in concepts.values():
#             concept["type"] = concept["object"].get_type().get_label().name
#
#             if concept["object"].is_attribute():
#                 concept["root-type"] = transaction.concepts.get_root_attribute_type().get_label().name
#                 concept["value"] = concept["object"].as_attribute().get_value()
#                 concept["value-type"] = str(concept["object"].get_type().get_value_type())
#
#             if concept["object"].is_entity():
#                 concept["root-type"] = transaction.concepts.get_root_entity_type().get_label().name
#                 ownerships = [attribute.get_iid() for attribute in concept["object"].get_has(transaction)]
#                 concept["ownerships"] = [concepts[iid]["binding"] for iid in ownerships if iid in concepts.keys()]
#
#             if concept["object"].is_relation():
#                 concept["root-type"] = transaction.concepts.get_root_relation_type().get_label().name
#                 ownerships = [attribute.get_iid() for attribute in concept["object"].get_has(transaction)]
#                 concept["ownerships"] = [concepts[iid]["binding"] for iid in ownerships if iid in concepts.keys()]
#                 roleplayers = concept["object"].get_players_by_role_type(transaction)
#                 concept["roleplayers"] = list()
#
#                 for role in roleplayers.keys():
#                     for roleplayer in roleplayers[role]:
#                         iid = roleplayer.get_iid()
#
#                         if iid in concepts.keys():
#                             concept["roleplayers"].append((role.get_label().name, concepts[iid]["binding"]))
#
#             concept.pop("object")
#
#         serial = {concept["binding"]: concept for concept in concepts.values()}
#
#         for entry in serial.values():
#             entry.pop("binding")
#
#         return serial
#
#     @staticmethod
#     def _format_typeql(answer, answer_type, transaction):
#         if answer_type is ConceptRow:
#             concepts = Response._serialise_concepts(answer, transaction)
#             lines = list()
#
#             for binding, concept in concepts.items():
#                 lines.append("${} isa {};".format(binding, concept["type"]))
#
#                 if "value" in concept.keys():
#                     if concept["value-type"] == "string":
#                         lines.append("${} \"{}\";".format(binding, concept["value"]))
#                     elif concept["value-type"] == "datetime":
#                         lines.append("${} {};".format(binding, str(concept["value"]).replace(" ", "T")))
#                     else:
#                         lines.append("${} {};".format(binding, concept["value"]))
#
#                 if "ownerships" in concept.keys():
#                     for attribute_binding in concept["ownerships"]:
#                         lines.append("${} has ${};".format(binding, attribute_binding))
#
#                 if "roleplayers" in concept.keys():
#                     if len(concept["roleplayers"]) > 0:
#                         roleplayers = list()
#
#                         for roleplayer in concept["roleplayers"]:
#                             roleplayers.append("{}: ${}".format(roleplayer[0], roleplayer[1]))
#
#                         lines.append("${} ({});".format(binding, ", ".join(roleplayers)))
#
#             return "\n".join(lines)
#         elif answer_type in (ConceptDocumentIterator):
#             raise NotImplementedError("fetch")
#         else:
#             raise ValueError("Unknown answer type. Please report this error.")
#
#     @staticmethod
#     def _format(query, answer, answer_type, output_format, transaction):
#         if answer_type is OkQueryAnswer:
#             result = None
#             message = "Query executed successfully!"
#             return result, message
#         else:
#             if output_format == "json":
#                 result = Response._format_json(answer, answer_type)
#                 message = None
#             elif output_format == "typeql":
#                 raise NotImplementedError("typeql output")
#                 result = Response._format_typeql(answer, answer_type, transaction)
#                 message = None
#             else:
#                 raise ArgumentError("Unknown output format: '{}'".format(output_format))
#
#             return result, message
