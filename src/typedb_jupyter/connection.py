from typedb.client import TypeDB
from typedb.api.connection.session import SessionType
from typedb_jupyter.exception import ArgumentError


class Connection(object):
    current = None
    connections = dict()

    def __init__(self, address, database, alias, create_database):
        self.address = address
        self.database = database
        self.name = "{}@{}".format(database, address)

        if alias is None:
            self.alias = self.name
            self.verbose_name = self.name
        else:
            self.alias = alias
            self.verbose_name = "{} ({})".format(self.alias, self.name)

        client = TypeDB.core_client(address)

        if not client.databases().contains(database):
            if create_database:
                client.databases().create(database)
                print("Created database: {}".format(self.name))
            else:
                raise ArgumentError("Database with name '{}' does not exist and automatic database creation has been disabled.".format(database))

        self.client = client
        self.session = client.session(database, SessionType.DATA)

        self.connections[self.name] = self

    def __del__(self):
        try:
            self.session.close()
        finally:
            self.client.close()

    @classmethod
    def _aliases(cls):
        return [cls.connections[name].alias for name in cls.connections]

    @classmethod
    def _get_current(cls):
        if len(cls.connections) == 0:
            raise ArgumentError(
                "No database connection exists. Use -a and -d to specify server address and database name.")
        elif cls.current is None:
            raise ArgumentError(
                "Current connection was closed. Use -l to list connections and -n to select connection.")

        return cls.current

    @classmethod
    def _get_by_alias(cls, alias):
        try:
            return {cls.connections[name].alias: cls.connections[name] for name in cls.connections}[alias]
        except KeyError:
            raise ArgumentError("Connection name not recognised. Use -l to list connections.")

    @classmethod
    def set(cls, args, create_database):
        if args.database is None and args.alias is None:
            if args.address is not None:
                raise ArgumentError("Cannot open connection without a database name. Use -d to specify database.")
            else:
                cls.display()

        elif args.database is None:
            cls.current = cls._get_by_alias(args.alias)
            print("Selected connection: {}".format(cls.current.verbose_name))

        else:
            if args.address is None:
                args.address = TypeDB.DEFAULT_ADDRESS

            if "{}@{}".format(args.database, args.address) in cls.connections:
                raise ArgumentError("Cannot open more than one connection to the same database. Use -c to close opened connection first.")

            cls.current = Connection(args.address, args.database, args.alias, create_database)
            print("Opened connection: {}".format(cls.current.verbose_name))

    @classmethod
    def get(cls):
        return cls._get_current()

    @classmethod
    def display(cls):
        print("Current connection: {}".format(cls._get_current().verbose_name))

    def set_session(self, session_type):
        if self.session.session_type() != session_type:
            self.session.close()
            self.session = self.client.session(self.database, session_type)
            if session_type == SessionType.SCHEMA:
                session_arg = "schema"
            else:
                session_arg = "data"
            print("Switched to {} session for connection: {}".format(session_arg, self.verbose_name))
            return

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
    def close(cls, alias, delete):
        connection = cls._get_by_alias(alias)
        verbose_name = connection.verbose_name

        if cls.current.alias == alias:
            cls.current = None

        connection = cls.connections[connection.name]

        if delete:
            connection.session.close()
            connection.client.databases().get(connection.database).delete()
            print("Deleted database: {}".format(connection.name))

        del cls.connections[connection.name]
        print("Closed connection: {}".format(verbose_name))
