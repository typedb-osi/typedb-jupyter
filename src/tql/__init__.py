from .magic import TQLMagic


def load_ipython_extension(ipython):
    ipython.register_magics(TQLMagic)
