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

import re
from traitlets.config.configurable import Configurable
from traitlets import Bool
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class, needs_local_scope
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from typedb_jupyter.connection import Connection
from typedb_jupyter.exception import ArgumentError, QueryParsingError

import typedb_jupyter.subcommands as subcommands

@magics_class
class TypeDBMagic(Magics, Configurable):
    create_database = Bool(
        True,
        config=True,
        help="Create database when opening a connection if it does not already exist."
    )


    @line_magic("typedb")
    def execute(self, line=""):
        args = line.split(" ")
        if len(args) > 0:
            command_name = args[0].lower()
            if command_name in subcommands.AVAILABLE_COMMANDS:
                subcommand = subcommands.AVAILABLE_COMMANDS[args[0]]
            else:
                print("Unrecognised command: ", args[0])
                subcommand = subcommands.Help
        else:
            subcommand = subcommands.Help

        try:
            return subcommand.execute(args[1:])
        except subcommands.CommandParsingError as err:
            print("Exception with subcommand: ", err.msg)
            return err

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add ourselves to the list of module configurable via %config
        self.shell.configurables.append(self)


@magics_class
class TypeQLMagic(Magics, Configurable):
    show_info = Bool(
        True,
        config=True,
        help="Always show full connection information when executing a query."
    )
    strict_transactions = Bool(
        False,
        config=True,
        help="Require transaction types to be specified for every transaction."
    )
    global_inference = Bool(
        False,
        config=True,
        help="Enable rule inference for all queries. Can be overridden per query with -i."
    )

    QUERY_RESULT_VARIABLE = "_typeql_result"

    @needs_local_scope
    @cell_magic("typeql")
    @magic_arguments()
    def execute(self, line="", cell="", local_ns=None):
        if local_ns is None:
            local_ns = {}

        args = parse_argstring(self.execute, line)
        query = cell

        # Save globals and locals, so they can be referenced in bind vars
        user_ns = self.shell.user_ns.copy()
        user_ns.update(local_ns)

        if query.strip() == "":
            raise ArgumentError("No query string supplied.")

        connection = Connection.get()
        tx = connection.get_active_transaction()
        answer_type, answer = self._run_query(tx, query)
        self._print_answers(answer_type, answer)

        self.shell.user_ns.update({self.QUERY_RESULT_VARIABLE: answer})
        return "Stored result in variable: {}".format(self.QUERY_RESULT_VARIABLE)

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add ourselves to the list of module configurable via %config
        self.shell.configurables.append(self)

    def _run_query(self, transaction, query):
        from typedb.concept.answer.concept_row_iterator import ConceptRowIterator
        from typedb.concept.answer.concept_document_iterator import ConceptDocumentIterator
        from typedb.concept.answer.ok_query_answer import OkQueryAnswer
        answer = transaction.query(query).resolve()
        if answer.is_concept_rows():
            return (ConceptRowIterator, list(answer.as_concept_rows()))
        elif answer.is_concept_documents():
            return (ConceptDocumentIterator, list(answer.as_concept_documents()))
        elif answer.is_ok():
            return (OkQueryAnswer, None)
        else:
            raise NotImplementedError("Unhandled answer type")


    def _print_answers(self, answer_type, answer):
        from typedb.concept.answer.concept_row_iterator import ConceptRowIterator
        from typedb.concept.answer.concept_document_iterator import ConceptDocumentIterator
        from typedb.concept.answer.ok_query_answer import OkQueryAnswer
        from typedb_jupyter.display import print_rows, print_documents
        if answer_type == OkQueryAnswer:
            print("Query completed successfully! (No results to show)")
        elif answer_type == ConceptDocumentIterator:
            print_documents(answer)
        elif answer_type == ConceptRowIterator:
            print_rows(answer)
        else:
            raise NotImplementedError("Unhandled answer type")
