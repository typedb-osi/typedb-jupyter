# TypeDB Jupyter connector

## Version 0.3

- The `%tql` magic command has been replaced with two new ones: `%typedb` and `%typeql`. `%typedb` is used for opening 
and managing connections to TypeDB servers, and `%typeql` is used for executing queries. Multiline queries now use
`%%typeql` accordingly.
- TypeDB Cloud and Cluster are now supported. Connecting to a Cloud/Cluster server can be done using `-d` to specify
database name and `-a` to specify server address as with TypeDB Core servers, in addition to the new arguments `-u`,
`-p`, and `-c` for specifying username, password, and TLS certificate path respectively.
- The arguments for closing connections and deleting databases have changed from `-c` to `-k` and from `-k` to `-x`
respectively. `-c` is now used for TLS certificate path when connecting to TypeDB Cloud/Cluster.
- More information about query execution is now provided to the user. This can be disabled with
`%config TypeQLMagic.show_info = False`.

## Version 0.2

- Initial release.