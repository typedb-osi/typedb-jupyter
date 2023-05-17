from .magic import TypeDBMagic, TypeQLMagic


def load_ipython_extension(ipython):
    ipython.register_magics(TypeDBMagic)
    ipython.register_magics(TypeQLMagic)
