# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import logging

from lab import B
from plum import Dispatcher, Self, Referentiable, type_parameter

from .cache import cache, Cache
from .input import At, MultiInput, Input
from .kernel import Kernel
from .matrix import dense, Dense, Zero, Diagonal, One

__all__ = ['MultiOutputKernel']

log = logging.getLogger(__name__)


class MultiOutputKernel(Kernel, Referentiable):
    """A generic multi-output kernel.

    Args:
        *ps (instance of :class:`.graph.GP`): Processes that make up the
            multi-valued process.
    """
    _dispatch = Dispatcher(in_class=Self)

    def __init__(self, *ps):
        self.kernels = ps[0].graph.kernels
        self.ps = ps

    @_dispatch({B.Numeric, Input}, {B.Numeric, Input}, Cache)
    @cache
    def __call__(self, x, y, B):
        return self(MultiInput(*(p(x) for p in self.ps)),
                    MultiInput(*(p(y) for p in self.ps)), B)

    @_dispatch(At, {B.Numeric, Input}, Cache)
    @cache
    def __call__(self, x, y, B):
        return self(MultiInput(x), MultiInput(*(p(y) for p in self.ps)), B)

    @_dispatch({B.Numeric, Input}, At, Cache)
    @cache
    def __call__(self, x, y, B):
        return self(MultiInput(*(p(x) for p in self.ps)), MultiInput(y), B)

    @_dispatch(At, At, Cache)
    @cache
    def __call__(self, x, y, B):
        return self.kernels[type_parameter(x),
                            type_parameter(y)](x.get(), y.get(), B)

    @_dispatch(MultiInput, At, Cache)
    @cache
    def __call__(self, x, y, B):
        return self(x, MultiInput(y), B)

    @_dispatch(At, MultiInput, Cache)
    @cache
    def __call__(self, x, y, B):
        return self(MultiInput(x), y, B)

    @_dispatch(MultiInput, MultiInput, Cache)
    @cache
    def __call__(self, x, y, B):
        return B.block_matrix(*[[self(xi, yi, B) for yi in y.get()]
                                for xi in x.get()])

    @_dispatch({B.Numeric, Input}, {B.Numeric, Input}, Cache)
    @cache
    def elwise(self, x, y, B):
        return self.elwise(MultiInput(*(p(x) for p in self.ps)),
                           MultiInput(*(p(y) for p in self.ps)), B)

    @_dispatch(At, {B.Numeric, Input}, Cache)
    @cache
    def elwise(self, x, y, B):
        raise ValueError('Unclear combination of arguments given to '
                         'MultiOutputKernel.elwise.')

    @_dispatch({B.Numeric, Input}, At, Cache)
    @cache
    def elwise(self, x, y, B):
        raise ValueError('Unclear combination of arguments given to '
                         'MultiOutputKernel.elwise.')

    @_dispatch(At, At, Cache)
    @cache
    def elwise(self, x, y, B):
        return self.kernels[type_parameter(x),
                            type_parameter(y)].elwise(x.get(), y.get(), B)

    @_dispatch(MultiInput, At, Cache)
    @cache
    def elwise(self, x, y, B):
        raise ValueError('Unclear combination of arguments given to '
                         'MultiOutputKernel.elwise.')

    @_dispatch(At, MultiInput, Cache)
    @cache
    def elwise(self, x, y, B):
        raise ValueError('Unclear combination of arguments given to '
                         'MultiOutputKernel.elwise.')

    @_dispatch(MultiInput, MultiInput, Cache)
    @cache
    def elwise(self, x, y, B):
        if len(x.get()) != len(y.get()):
            raise ValueError('MultiOutputKernel.elwise must be called with '
                             'similarly sized MultiInputs.')
        return B.concat([self.elwise(xi, yi, B)
                         for xi, yi in zip(x.get(), y.get())], axis=0)

    def __str__(self):
        ks = [str(self.kernels[p]) for p in self.ps]
        return 'MultiOutputKernel({})'.format(', '.join(ks))
