# TypeDB Jupyter connector

Runs TypeQL statements against a TypeDB database from a Jupyter notebook using the `%typedb` and `%typeql` IPython magic
commands.

## Getting started

Install this module with:

```
pip install typedb-jupyter
```

or your environment equivalent. Load the extension in Jupyter with:

```
%load_ext typedb_jupyter
```

## Connecting to TypeDB

Establish a connection with:

```
%typedb -d <database name> [-a <server address>] [-n <connection alias>]
```

for example:

```
In [1]: %typedb -a 111.111.111.111:1729 -d database_1

Out[1]: Opened connection: database_1@111.111.111.111:1729
```


```
In [2]: %typedb -a 222.222.222.222:1729 -d database_2 -n test_connection

Out[2]: Opened connection: test_connection (database_2@222.222.222.222:1729)
```


```
In [3]: %typedb -d database_local

Out[3]: Opened connection: database_local@localhost:1729
```

If no address is provided, the default `localhost:1729` will be used. If no custom alias is provided, the connection
will be assigned a default alias of the format `<database name>@<server address>`. Custom aliases can only include
alphanumeric characters, hyphens, and underscores. If a connection with the server is established but no database with
the name provided exists, a new database will be created with that name by default. Only one connection can be opened to
each database at a time.

For connecting to TypeDB Cluster, use:

```
%typedb -d <database name> -a <server address> -u <username> -p <password> -c <certificate path> [-n <connection alias>]
```

List established connections with:

```
In [4]: %typedb -l

Out[4]: Open connections:
   ...:    database_1@111.111.111.111:1729
   ...:    test_connection (database_2@222.222.222.222:1729)
   ...:  * database_local@localhost:1729
```

An asterisk appears next to the currently selected connection, which is the last one opened by default. To change the
selected connection, use:

```
%typedb -n <connection alias>
```

for example:

```
In [5]: %typedb -n database_1@111.111.111.111:1729

Out[5]: Selected connection: database_1@111.111.111.111:1729
```

```
In [6]: %typedb -n test_connection

Out[6]: Selected connection: test_connection
```

Close a connection with:

```
%typedb -k <connection name>
```

for example:

```
In [7]: %typedb -c database_2@222.222.222.222:1729

Out[7]: Closed connection: database_2@222.222.222.222:1729
```

If the currently selected connection is closed, a new one must be manually selected before queries can be executed.
Using `-x` instead of `-k` will also delete the database.

## Executing a query

Run a query against a database using the selected connection with:

```
%typeql <typeql string>
```

or

```
%%typeql <multiline typeql string>
```

For example:

```
In [8]: %typeql match $p isa person;

Out[8]: [{'p': {'type': 'person'}},
   ...:  {'p': {'type': 'person'}}]
```

```
In [9]: %%typeql
   ...: match
   ...:   $p isa person,
   ...:   has name $n,
   ...:   has age $a;

Out[9]: [{'a': {'type': 'age', 'value_type': 'long', 'value': 30},
   ...:   'p': {'type': 'person'},
   ...:   'n': {'type': 'name', 'value_type': 'string', 'value': 'Kevin'}},
   ...:  {'a': {'type': 'age', 'value_type': 'long', 'value': 50},
   ...:   'p': {'type': 'person'},
   ...:   'n': {'type': 'name', 'value_type': 'string', 'value': 'Gavin'}}]
```

Results of read queries are returned in a JSON-like native Python object. The shape of the object is dependent on the
type of query, as described in the following table:

| Query type              | Output object type |
|-------------------------|--------------------|
| `match`                 | `list<dict>`       |
| `match-group`           | `dict<list<dict>>` |
| `match-aggregate`       | `intǀfloat`        |
| `match-group-aggregate` | `dict<intǀfloat>`  |

Queries automatically interpolate variables from the notebook's Python namespace, specified using the syntax
`{<variable name>}`, for example:

```
In [10]: age = 30

In [11]: %typeql match $p isa person, has name $n, has age {age}; count;

Out[11]: 1
```

Similarly, results can be saved to a namespace variable by providing the variable name with:

```
%typeql -r <variable name> <typeql string>
```

for example:

```
In [12]: %typeql -r name_counts match $p isa person, has name $n, has age $a; group $n; count;

In [13]: name_counts

Out[13]: {'Gavin': 1, 'Kevin': 1}
```

To execute a query in a stored TypeQL file, supply the filepath with:

```
%typeql -f <file path>
```

Rule inference is disabled by default. It can be enabled for a query with:

```
%typeql -i True <tql>
```

In order to enable rule inference globally, see the [Configuring options](#configuring-options)
section below.

## Information for advanced users

Queries are syntactically analysed to automatically determine schema and transaction types, but these can be overridden
with:

```
%typeql [-s <session type>] [-t <transaction type>] <typeql string>
```

where `<session type>` is either `schema` or `data`, and `<transaction type>` is either `read` or `write`.

When a connection is instantiated, a data session is opened and persisted for the duration of the connection unless a
schema query is issued, at which point the data session is closed and a schema session is opened. After the schema query
has been executed, the schema session is then closed and a new data session opened. Each call of `%typeql` or `%%typeql`
is executed in a new transaction, which is then immediately closed on completion. All clients, sessions, and
transactions are closed automatically when the notebook's kernel is terminated.

It is important to note that TypeDB sessions and transactions cannot be opened under certain conditions, regardless of
the client:

- Only one schema session can be opened at any time.
- Data write transactions cannot be opened while a schema session is open.
- Only one schema write transaction can be opened at any time.

This means that, when a `define` or `undefine` query is executed in a notebook, this will interfere with queries
performed by other users.

## Configuring options

Certain options can be configured using the `%config` magic with:

```
%config <config argument>`
```

After being set, these options persist for the remainder of the notebook unless
changed again. The following table describes the available arguments:

| Argument                                      | Usage                                                                         | Default |
|-----------------------------------------------|-------------------------------------------------------------------------------|---------|
| `TypeDBMagic`                                 | List config options and current set values for `%typedb`.                     |         |
| `TypeDBMagic.create_database = <boolean>`     | Create database when opening a connection if it does not already exist.       | `True`  |
| `TypeQLMagic`                                 | List config options and current set values for `%typeql`.                     |         |
| `TypeQLMagic.global_inference = <boolean>`    | Enable rule inference for all queries. Can be overridden per query with `-i`. | `False` |
| `TypeQLMagic.show_info = <boolean>`           | Always show full connection information when executing a query.               | `True`  |
| `TypeQLMagic.strict_transactions = <boolean>` | Require session and transaction types to be specified for every transaction.  | `False` |

## Command glossary 

The following tables list the arguments that can be provided to the `%typedb` and `%typeql` magic commands:

| Magic command | Argument                | Usage                                                                       |
|---------------|-------------------------|-----------------------------------------------------------------------------|
| `%typedb`     | `-a <server address>`   | TypeDB server address for new connection.                                   |
| `%typedb`     | `-d <database name>`    | Database name for new connection.                                           |
| `%typedb`     | `-u <username>`         | Username for new Cloud/Cluster connection.                                  |
| `%typedb`     | `-p <password>`         | Password for new Cloud/Cluster connection.                                  |
| `%typedb`     | `-c <certificate path>` | TLS certificate path for new Cloud/Cluster connection.                      |
| `%typedb`     | `-n <connection alias>` | Custom alias for new connection, or alias of existing connection to select. |
| `%typedb`     | `-l`                    | List currently open connections.                                            |
| `%typedb`     | `-k <connection name>`  | Close a connection by name.                                                 |
| `%typedb`     | `-x <connection name>`  | Close a connection by name and delete its database.                         |
| `%typeql`     | `-r <variable name>`    | Assign query result to the named variable instead of printing.              |
| `%typeql`     | `-f <file path>`        | Read in query from a TypeQL file at the specified path.                     |
| `%typeql`     | `-i <inference option>` | Enable (`True`) or disable (`False`) rule inference for query.              |
| `%typeql`     | `-s <session type>`     | Force a particular session type for query, `schema` or `data`.              |
| `%typeql`     | `-t <transaction type>` | Force a particular transaction type for query, `read` or `write`.           |

## Planned features

- Add option to close all connections.
- Add more output formats.

## Acknowledgements

Many thanks to Catherine Devlin and all the contributors to
[ipython-sql](https://github.com/catherinedevlin/ipython-sql), which served as
the basis for this project.