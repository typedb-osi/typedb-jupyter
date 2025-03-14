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

from typedb.driver import TypeDB, DriverOptions
from typedb_jupyter.exception import ArgumentError, ConnectionError

class Connection(object):
    current = None

    def __init__(self, driver, address, credential, tls_enabled):
        self.address = address
        if driver is TypeDB.core_driver:
            self.driver = TypeDB.core_driver(address, credential, DriverOptions(tls_enabled))
        elif driver is TypeDB.cloud_driver:
            self.driver = TypeDB.cloud_driver(address, credential, DriverOptions(tls_enabled))
        else:
            raise ValueError("Unknown client type. Please report this error.")
        self.active_transaction = None

    def __del__(self):
        if self.active_transaction is not None:
            self.active_transaction.close()
            self.active_transaction = None
        self.driver.close()

    @classmethod
    def open(cls, client, address, credential, tls_enabled):
        if cls.current is None:
            cls.current = Connection(client, address, credential, tls_enabled)
            print("Opened connection to: {}".format(cls.current.address))
        else:
            raise ArgumentError("Cannot open more than one connection. Use `connection close` to close opened connection first.")
    @classmethod
    def get(cls):
        return cls.current

    @classmethod
    def close(cls):
        connection = cls.current
        cls.current = None
        del connection
        print("Closed connection")

    def _ensure_transaction_open(self):
        if self.active_transaction is None:
            raise ArgumentError("There is no open transaction")
        elif not self.active_transaction.is_open():
            self.active_transaction = None
            raise ConnectionError("The transaction has been closed")

    def get_active_transaction(self):
        self._ensure_transaction_open()
        return self.active_transaction

    def open_transaction(self, database, transaction_type):
        if self.active_transaction is not None:
            raise ArgumentError("Cannot open a transaction when there is one active. Please close it first.")
        else:
            self.active_transaction = self.driver.transaction(database, transaction_type)


    def close_transaction(self):
        self._ensure_transaction_open()
        self.active_transaction.close()
        self.active_transaction = None

    def commit_transaction(self):
        self._ensure_transaction_open()
        self.active_transaction.commit()
        self.active_transaction = None


    def rollback_transaction(self):
        self._ensure_transaction_open()
        self.active_transaction.rollback()
        self.active_transaction = None
