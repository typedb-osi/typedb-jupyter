from typedb.api.connection.credential import TypeDBCredential
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
        cluster_args = (args.username, args.password, args.certificate)

        if args.database is None:
            if args.address is not None or not all(arg is None for arg in cluster_args):
                raise ArgumentError("Cannot open connection without a database name. Use -d to specify database.")

            if args.alias is None:
                print("Current connection: {}".format(cls._get_current().verbose_name))
            else:
                cls.current = cls._get_by_alias(args.alias)
                print("Selected connection: {}".format(cls.current.verbose_name))
        else:
            if all(arg is None for arg in cluster_args):
                client = TypeDB.core_client
                credential = None
            elif all(arg is not None for arg in cluster_args):
                client = TypeDB.cluster_client
                credential = TypeDBCredential(args.username, args.password, args.certificate)
            else:
                raise ArgumentError("Cannot open cluster connection without a username, password, and certificate path. Use -u, -p, and -c to specify these.")

            if args.address is None:
                args.address = TypeDB.DEFAULT_ADDRESS

            if "{}@{}".format(args.database, args.address) in cls.connections:
                raise ArgumentError("Cannot open more than one connection to the same database. Use -c to close opened connection first.")

            cls.current = Connection(client, args.address, args.database, credential, args.alias, create_database)
            print("Opened connection: {}".format(cls.current.verbose_name))

    @classmethod
    def get(cls):
        return cls._get_current()

    def set_session(self, session_type):
        if self.session.session_type() != session_type:
            self.session.close()
            self.session = self.client.session(self.database, session_type)
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

        if cls.current is not None and cls.current.alias == alias:
            cls.current = None

        connection = cls.connections[connection.name]

        if delete:
            connection.session.close()
            connection.client.databases().get(connection.database).delete()
            print("Deleted database: {}".format(connection.database))

        del cls.connections[connection.name]
        print("Closed connection: {}".format(verbose_name))
