from traitlets.config.configurable import Configurable
from traitlets import Bool
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class, needs_local_scope
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from typedb.api.connection.credential import TypeDBCredential
from typedb.client import TypeDB
from typedb_jupyter.connection import Connection
from typedb_jupyter.query import Query
from typedb_jupyter.exception import ArgumentError, QueryParsingError


def substitute_vars(query, local_ns):
    try:
        query_vars = "".join(query.split("\"")[::2]).replace("{", "}").split("}")[1::2]
    except IndexError:
        return query

    for var in query_vars:
        try:
            val = local_ns[var]
        except KeyError:
            raise QueryParsingError("No variable found in local namespace with name: {}".format(var))

        if type(val) is str:
            val = "\"{}\"".format(val.replace("\"", "'"))
        else:
            val = str(val)

        query = query.replace("{" + var + "}", val)

    return query


@magics_class
class TypeDBMagic(Magics, Configurable):
    create_database = Bool(
        True,
        config=True,
        help="Create database when opening a connection if it does not already exist."
    )

    @line_magic("typedb")
    @magic_arguments()
    @argument("-a", "--address", type=str, help="TypeDB server address for new connection.")
    @argument("-d", "--database", type=str, help="Database name for new connection.")
    @argument("-u", "--username", type=str, help="Username for new Cloud/Cluster connection.")
    @argument("-p", "--password", type=str, help="Password for new Cloud/Cluster connection.")
    @argument("-c", "--certificate", type=str, help="TLS certificate path for new Cloud/Cluster connection.")
    @argument("-n", "--alias", type=str, help="Alias for new connection, or alias of existing connection to select.")
    @argument("-l", "--list", action="store_true", help="List currently open connections.")
    @argument("-k", "--close", type=str, help="Close a connection by name.")
    @argument("-x", "--delete", type=str, help="Close a connection by name and delete its database.")
    def execute(self, line=""):
        args = parse_argstring(self.execute, line)

        if args.list:
            return Connection.list()
        elif args.delete:
            return Connection.close(args.delete, delete=True)
        elif args.close:
            return Connection.close(args.close)
        else:
            cluster_args = (args.username, args.password, args.certificate)

            if args.database is None:
                if args.address is not None or not all(arg is None for arg in cluster_args):
                    raise ArgumentError("Cannot open connection without a database name. Use -d to specify database.")
                elif args.alias is None:
                    Connection.display()
                else:
                    Connection.select(args.alias)
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
                    address = TypeDB.DEFAULT_ADDRESS
                else:
                    address = args.address

                Connection.open(client, address, args.database, credential, args.alias, self.create_database)
            return

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
        help="Require session and transaction types to be specified for every transaction."
    )
    global_inference = Bool(
        False,
        config=True,
        help="Enable rule inference for all queries. Can be overridden per query with -i."
    )

    @needs_local_scope
    @line_magic("typeql")
    @cell_magic("typeql")
    @magic_arguments()
    @argument("line", default="", nargs="*", type=str, help="Valid TypeQL string.")
    @argument("-r", "--result", type=str, help="Assign query result to the named variable instead of printing.")
    @argument("-f", "--file", type=str, help="Read in query from a TypeQL file at the specified path.")
    @argument("-i", "--inference", type=bool, help="Enable (True) or disable (False) rule inference for query.")
    @argument("-s", "--session", type=str, help="Force a particular session type for query, 'schema' or 'data'.")
    @argument("-t", "--transaction", type=str, help="Force a particular transaction type for query, 'read' or 'write'.")
    def execute(self, line="", cell="", local_ns=None):
        if local_ns is None:
            local_ns = {}

        args = parse_argstring(self.execute, line)
        query = " ".join(args.line) + "\n" + cell
        query = substitute_vars(query, local_ns)

        # Save globals and locals, so they can be referenced in bind vars
        user_ns = self.shell.user_ns.copy()
        user_ns.update(local_ns)

        if args.file:
            with open(args.file, "r") as infile:
                query = infile.read() + "\n" + query

        if query.strip() == "":
            raise ArgumentError("No query string supplied.")

        connection = Connection.get()
        query = Query(query, args.session, args.transaction, args.inference, self.strict_transactions, self.global_inference)
        result = query.run(connection, self.show_info)

        if args.result:
            print("Returning data to local variable: '{}'".format(args.result))
            self.shell.user_ns.update({args.result: result})
            return

        # Return results into the default ipython _ variable
        return result

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add ourselves to the list of module configurable via %config
        self.shell.configurables.append(self)
