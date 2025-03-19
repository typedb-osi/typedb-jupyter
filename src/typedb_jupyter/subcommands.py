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
import abc
import argparse

from typedb_jupyter.exception import ArgumentError, CommandParsingError
from typedb.api.connection.transaction import TransactionType

def parser_exit_override(a, b):
    raise CommandParsingError(a, b)

class SubCommandBase(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def execute(cls, args):
        raise NotImplementedError("abstract")

    @classmethod
    def get_parser(cls):
        raise NotImplementedError("abstract")

    @classmethod
    def help(cls):
        cls.get_parser().print_help()

    @classmethod
    def name(cls):
        return str(cls.get_parser().prog)

    @classmethod
    def print_help(cls):
        print(cls.get_parser().format_help())

class Connect(SubCommandBase):
    _PARSER = None
    @classmethod
    def get_parser(cls):
        if cls._PARSER is None:
            parser = argparse.ArgumentParser(
                prog='connect',
                description='Establishes the connection to TypeDB'
            )
            parser.exit = parser_exit_override
            parser.add_argument("action", choices=["open", "close", "help"])
            parser.add_argument("kind", nargs='?', choices=["core", "cluster"])
            parser.add_argument("address", nargs='?', default="127.0.0.1:1729")
            parser.add_argument("username", nargs='?', default = "admin")
            parser.add_argument("password", nargs='?', default = "password")
            parser.add_argument("--tls-enabled",  action="store_true", help="Use for encrypted servers")
            cls._PARSER = parser
        return cls._PARSER

    @classmethod
    def execute(cls, args):
        from typedb.driver import TypeDB
        from typedb.api.connection.credentials import Credentials
        from typedb_jupyter.connection import Connection

        cmd = cls.get_parser().parse_args(args)
        if cmd.action == "help":
            cls.print_help()
        elif cmd.action == "open":
            driver = TypeDB.cloud_driver if cmd.kind == "cluster" else TypeDB.core_driver
            credential = Credentials(cmd.username, cmd.password)
            Connection.open(driver, cmd.address, credential, bool(cmd.tls_enabled))
        elif cmd.action == "close":
            Connection.close()
        else:
            raise NotImplementedError("Unimplemented for action: ", cmd.action)


class Database(SubCommandBase):
    _PARSER = None
    @classmethod
    def get_parser(cls):
        if cls._PARSER is None:
            parser = argparse.ArgumentParser(
                prog='database',
                description='Database management'
            )
            parser.exit = parser_exit_override
            parser.add_argument("action", choices=["create", "recreate", "list", "delete", "schema", "help"])
            parser.add_argument("name", nargs='?')
            cls._PARSER = parser
        return cls._PARSER

    @classmethod
    def execute(cls, args):
        from typedb_jupyter.connection import Connection

        cmd = cls.get_parser().parse_args(args)

        driver = Connection.get().driver
        if cmd.action == "help":
            cls.print_help()
        elif cmd.action == "create":
            driver.databases.create(cmd.name)
            print("Created database ", cmd.name)
        elif cmd.action == "recreate":
            if driver.databases.contains(cmd.name):
                driver.databases.get(cmd.name).delete()
            driver.databases.create(cmd.name)
            print("Recreated database ", cmd.name)
        elif cmd.action == "delete":
            driver.databases.get(cmd.name).delete()
            print("Deleted database ", cmd.name)
        elif cmd.action == "list":
            print("Databases: ", ", ".join(map(lambda db: db.name, driver.databases.all())))
        elif cmd.action == "schema":
            db = driver.databases.get(cmd.name)
            print("Schema for database: ", db.name)
            print(db.schema())
        else:
            raise NotImplementedError("Unimplemented for action: ", cmd.action)


class Transaction(SubCommandBase):
    _PARSER = None
    @classmethod
    def get_parser(cls):
        if cls._PARSER is None:
            parser = argparse.ArgumentParser(
                prog='transaction',
                description='Opens or closes a transaction to a database on the active connection'
            )
            parser.exit = parser_exit_override
            parser.add_argument("action", choices=["open", "close", "commit", "rollback", "help"])
            parser.add_argument("database", nargs='?', help="Only for 'open'")
            parser.add_argument("tx_type", nargs='?', choices=["schema", "write", "read"], help="Only for 'open'")
            cls._PARSER = parser
        return cls._PARSER

    TX_TYPE_MAP = {
        "schema": TransactionType.SCHEMA,
        "write": TransactionType.WRITE,
        "read": TransactionType.READ,
    }

    @classmethod
    def execute(cls, args):
        from typedb_jupyter.connection import Connection

        cmd = cls.get_parser().parse_args(args)

        connection = Connection.get()
        if cmd.action == "help":
            cls.print_help()
        elif cmd.action == "open":
            if cmd.database is None or cmd.tx_type is None:
                raise ArgumentError("transaction open database tx_type")
            connection.open_transaction(cmd.database, cls.TX_TYPE_MAP[cmd.tx_type])
            print("Opened {} transaction on database '{}'  ".format(cmd.tx_type, cmd.database))
        elif cmd.action == "close":
            connection.close_transaction()
            print("Transaction closed")
        elif cmd.action == "commit":
            connection.commit_transaction()
            print("Transaction committed")
        elif cmd.action == "rollback":
            connection.rollback_transaction()
            print("Transaction rolled back")
        else:
            raise NotImplementedError("Unimplemented for action: ", cmd.action)

class Help(SubCommandBase):
    _PARSER = None

    @classmethod
    def get_parser(cls):
        if cls._PARSER is None:
            parser = argparse.ArgumentParser(
                prog='help',
                description='Shows this help description'
            )
            parser.exit = parser_exit_override
            cls._PARSER = parser
        return cls._PARSER

    @classmethod
    def execute(cls, args):
        print("Available commands:", ", ".join(AVAILABLE_COMMANDS.keys()))
        if not (len(args) > 0 and args[0] == "short"):
            for subcommand in AVAILABLE_COMMANDS.values():
                print("-"*80)
                print("Help for command '%s':"%subcommand.name())
                subcommand.print_help()


AVAILABLE_COMMANDS  = {
    Connect.name() : Connect,
    Database.name() : Database,
    Transaction.name(): Transaction,
    Help.name(): Help,
}
