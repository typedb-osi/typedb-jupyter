from typedb.client import TypeDB
from typedb.api.connection.session import SessionType
from typedb_jupyter.exception import ArgumentError


class Connection(object):
    current = None
    connections = dict()

    def __init__(self, client, address, database, credential, alias, create_database):
        self.address = address
        self.database = database
        self.name = "{}@{}".format(database, address)

        if alias is None:
            self.alias = self.name
            self.verbose_name = self.name
        else:
            self.alias = alias
            self.verbose_name = "{} ({})".format(self.alias, self.name)

        if client is TypeDB.core_client:
            self.client = TypeDB.core_client(address)
        elif client is TypeDB.cluster_client:
            self.client = TypeDB.cluster_client(address, credential)
        else:
            raise ValueError("Unknown client type. Please report this error.")

        if not self.client.databases().contains(database):
            if create_database:
                self.client.databases().create(database)
                print("Created database: {}".format(self.database))
            else:
                raise ArgumentError("Database with name '{}' does not exist and automatic database creation has been disabled.".format(database))

        self.session = self.client.session(database, SessionType.DATA)
        self.connections[self.name] = self

    def __del__(self):
        try:
            self.session.close()
        finally:
            self.client.close()

    @classmethod
    def _get_current(cls):
        if len(cls.connections) == 0:
            raise ArgumentError("No database connection exists. Use -a and -d to specify server address and database name.")
        elif cls.current is None:
            raise ArgumentError("Current connection was closed. Use -l to list connections and -n to select connection.")

        return cls.current

    @classmethod
    def _get_by_alias(cls, alias):
        try:
            return {cls.connections[name].alias: cls.connections[name] for name in cls.connections}[alias]
        except KeyError:
            raise ArgumentError("Connection name not recognised. Use -l to list connections.")

    @classmethod
    def open(cls, client, address, database, credential, alias, create_database):
        if "{}@{}".format(database, address) in cls.connections:
            raise ArgumentError("Cannot open more than one connection to the same database. Use -c to close opened connection first.")
        else:
            cls.current = Connection(client, address, database, credential, alias, create_database)
            print("Opened connection: {}".format(cls.current.verbose_name))

    @classmethod
    def select(cls, alias):
        cls.current = cls._get_by_alias(alias)
        print("Selected connection: {}".format(cls.current.verbose_name))

    @classmethod
    def get(cls, alias=None):
        if alias is None:
            return cls._get_current()
        else:
            return cls._get_by_alias(alias)

    @classmethod
    def display(cls):
        print("Current connection: {}".format(cls._get_current().verbose_name))

    @classmethod
    def list(cls):
        if len(cls.connections) == 0:
            print("No open connections.")
        else:
            print("Open connections:")
            for name in sorted(cls.connections):
                if cls.connections[name] == cls.current:
                    prefix = " * "
                else:
                    prefix = "   "

                print("{}{}".format(prefix, cls.connections[name].verbose_name))

    @classmethod
    def set_session(cls, session_type, alias=None):
        connection = cls.get(alias)
        if connection.session.session_type() != session_type:
            connection.session.close()
            connection.session = connection.client.session(connection.database, session_type)

    @classmethod
    def close(cls, alias=None, delete=False):
        connection = cls.get(alias)
        verbose_name = connection.verbose_name

        if cls.current is not None and cls.current.alias == alias:
            cls.current = None

        connection = cls.connections[connection.name]

        if delete:
            connection.session.close()
            connection.client.databases().get(connection.database).delete()
            print("Deleted database: {}".format(connection.database))

        del cls.connections[connection.name]
        print("Closed connection: {}".format(verbose_name))
