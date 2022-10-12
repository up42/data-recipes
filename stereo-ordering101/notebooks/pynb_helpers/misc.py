# Sinple module with helper functions for working with jupyter
# notebooks.

# Get the function signature.
from inspect import signature as sig
from inspect import Signature

def methods(cls: object) -> list[(str, Signature)]:
    """Lists all non magic methods of a given class with
       their signatures.

    Similar to Julia's methods function.
    https://docs.julialang.org/en/v1/base/base/#Base.methods

    Parameters
    ----------
    cls : object
        Class for which we want to list the methods.

    Returns
    -------
    list[(str, inspect.Signature)]
        A list of pairs (tuples) of non-magic methods for the given
        class and their respective signatures.

    Examples
    --------
    class Foo:
        bar = 42

        def baz(self) -> float:
            return self.bar * 1.42

    methods(Foo) returns [("baz", <Signature (self: Foo) -> float>)]

    """
    return [ (x, sig(y)) for x, y in cls.__dict__.items()
             if type(y) == type(lambda:None) and not x.startswith("__") ]
