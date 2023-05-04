# TypeDB Jupyter connector

Runs TypeQL statements against a TypeDB database from a Jupyter notebook
using the `%tql` IPython magic command.

## Getting started

Install this module with:

```
pip install typedb-jupyter
```

or your environment equivalent. Load the extension in Jupyter with:

```
%load_ext tql
```

## Connecting to TypeDB

Establish a connection with:

```
%tql -d <database name> [-a <server address>] [-n <connection name>]
```

for example:

```
In [1]: %tql -a 111.111.111.111:1729 -d database_1

Out[1]: Opened connection: database_1@111.111.111.111:1729
```


```
In [2]: %tql -a 222.222.222.222:1729 -d database_2 -n test_connection

Out[2]: Opened connection: test_connection (database_2@222.222.222.222:1729)
```


```
In [3]: %tql -d database_local

Out[3]: Opened connection: database_local@localhost:1729
```

If no address is provided, the default `localhost:1729` will be used. If
no connection name is provided, the connection will be assigned a name
of the format `<database name>@<server address>`. If a connection with
the server is established but no database with the name provided exists,
a new database will be created with that name. Only one connection can
be opened to each database at a time.

List established connections with:

```
In [4]: %tql -l

Out[4]: Open connections:
   ...:    database_1@111.111.111.111:1729
   ...:    test_connection (database_2@222.222.222.222:1729)
   ...:  * database_local@localhost:1729
```

An asterisk appears next to the currently selected connection, which is
the last one opened by default. To change the selected connection, use:

```
%tql -n <connection name>
```

for example:

```
In [5]: %tql -n database_1@111.111.111.111:1729

Out[5]: Selected connection: database_1@111.111.111.111:1729
```

```
In [6]: %tql -n test_connection

Out[6]: Selected connection: test_connection
```

Close a connection with:

```
%tql -c <connection name>
```

for example:

```
In [7]: %tql -c database_2@222.222.222.222:1729

Out[7]: Closed connection: database_2@222.222.222.222:1729
```

If the currently selected connection is closed, a new one must be
manually selected. Using `-k` instead of `-c` will also delete the
database.

## Executing a query

Run a query against the database using the selected connection with:

```
%tql <tql>
```

or

```
%%tql <multiline tql>
```

For example:

```
In [8]: %tql match $p isa person;

Out[8]: [{'p': {'type': 'person'}},
   ...:  {'p': {'type': 'person'}}]
```

```
In [9]: %%tql
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

Results of read queries are returned in a JSON-like native Python
object. The shape of the object is dependent on the type of query, as
described in the following table:

| Query type              | Output object type     |
|-------------------------|------------------------|
| `match`                 | `list<dict>`           |
| `match-group`           | `dict<list<dict>>`     |
| `match-aggregate`       | `int&#124;float`       |
| `match-group-aggregate` | `dict<int&#124;float>` |

A connection can be opened or selected in the same call it is utilised with
`-d`, `-a`, and `-n` as specified above. Queries automatically interpolate
variables from the notebook's Python namespace, specified using the syntax
`{<variable name>}`, for example:

```
In [10]: age = 30

In [11]: %tql match $p isa person, has name $n, has age {age}; count;

Out[11]: 1
```

Similarly, results can be saved to a namespace variable by providing the variable
name with:

```
%tql -r <variable name> <tql>
```

for example:

```
In [12]: %tql -r name_counts match $p isa person, has name $n, has age $a; group $n; count;

In [13]: name_counts

Out[13]: {'Gavin': 1, 'Kevin': 1}
```

To execute a query in a stored TypeQL file, supply the filepath with:

```
%tql -f <file path>
```

Rule inference is disabled by default. It can be enabled for a query with:

```
%tql -i True <tql>
```

In order to enable rule inference globally, see the [Configuring options](#configuring-options)
section below.

## Information for advanced users

Queries are syntactically analysed to automatically
determine schema and transaction types, but these can be
overridden with:

```
%tql [-s <session type>] [-t <transaction type>] <tql>
```

where `<session type>` is either `schema` or `data`, and `<transaction type>`
is either `read` or `write`.

When a connection is instantiated, a data
session is opened and persisted for the duration of the connection unless the
required session type changes. Each call of `%tql` or `%%tql` is executed in
a new transaction, which is then immediately closed on completion. If a query
is executed requiring a different session type to the one open, the open
session is closed and a new one of the correct type is opened and persisted.
All sessions and clients are closed automatically when the notebook's kernel
is terminated. Note that opening a schema session to a TypeDB server requires
that no other sessions be open, regardless of the client used, and once open,
no other sessions can be opened on the server until the schema session is closed.

## Configuring options

Certain options can be configured using the `%config` magic with:

```
%config <config argument>`
```

After being set, these options persist for the remainder of the notebook unless
changed again. The following table describes the available arguments:

| Argument                                 | Usage                                                                         | Default |
|------------------------------------------|-------------------------------------------------------------------------------|---------|
| `TQLMagic`                               | List config options and current set values.                                   |         |
| `TQLMagic.create_database=<boolean>`     | Create database when opening a connection if it does not already exist.       | `True`  |
| `TQLMagic.global_inference=<boolean>`    | Enable rule inference for all queries. Can be overridden per query with `-i`. | `False` |
| `TQLMagic.show_connection=<boolean>`     | Always show current connection name when executing a query.                   | `True`  |
| `TQLMagic.strict_transactions=<boolean>` | Require session and transaction types to be specified for every transaction.  | `False` |

## Command glossary 

The following tables list the arguments that can be provided to the `%tql` magic command:

| Argument                | Usage                                                                         | Argument type        |
|-------------------------|-------------------------------------------------------------------------------|----------------------|
| `-a <server address>`   | TypeDB server address for new connection.                                     | Connection argument. |
| `-d <database name>`    | Database name for new connection.                                             | Connection argument. |
| `-n <connection name>`  | Custom name for new connection, or name of existing connection to select.     | Connection argument. |
| `-l`                    | List currently open connections.                                              | Connection argument. |
| `-c <connection name>`  | Close a connection by name.                                                   | Connection argument. |
| `-k <connection name>`  | Close a connection by name and delete its database.                           | Connection argument. |
| `-p <thread count>`     | Number of server communication threads for new connection (advanced feature). | Connection argument. |
| `-r <variable name>`    | Assign query result to the named variable instead of printing.                | Query argument.      |
| `-f <file path>`        | Read in query from a TypeQL file at the specified path.                       | Query argument.      |
| `-i <inference option>` | Enable (`True`) or disable (`False`) rule inference for query.                | Query argument.      |
| `-s <session type>`     | Force a particular session type for query, `schema` or `data`.                | Query argument.      |
| `-t <transaction type>` | Force a particular transaction type for query, `read` or `write`.             | Query argument.      |




## Planned features

- Add option to close all connections.
- Add more output formats.

## Acknowledgements

Many thanks to Catherine Devlin and all the contributors to
[ipython-sql](https://github.com/catherinedevlin/ipython-sql), which served as
the basis for this project.