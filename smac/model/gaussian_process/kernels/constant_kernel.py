from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import math
from inspect import Signature, signature

import numpy as np
import scipy.optimize
import scipy.spatial.distance
import scipy.special
import sklearn.gaussian_process.kernels as kernels

from smac.model.gaussian_process.kernels.magic_mixin_kernel import MagicMixin
from smac.model.gaussian_process.priors.prior import Prior

__copyright__ = "Copyright 2022, automl.org"
__license__ = "3-clause BSD"


class ConstantKernel(MagicMixin, kernels.ConstantKernel):
    def __init__(
        self,
        constant_value: float = 1.0,
        constant_value_bounds: Tuple[float, float] = (1e-5, 1e5),
        operate_on: Optional[np.ndarray] = None,
        prior: Optional[Prior] = None,
        has_conditions: bool = False,
    ) -> None:

        super(ConstantKernel, self).__init__(constant_value=constant_value, constant_value_bounds=constant_value_bounds)
        self.set_active_dims(operate_on)
        self.prior = prior
        self.has_conditions = has_conditions

    def _call(
        self,
        X: np.ndarray,
        Y: Optional[np.ndarray] = None,
        eval_gradient: bool = False,
        active: Optional[np.ndarray] = None,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """Return the kernel k(X, Y) and optionally its gradient.

        Parameters
        ----------
        X : array, shape (n_samples_X, n_features)
            Left argument of the returned kernel k(X, Y)

        Y : array, shape (n_samples_Y, n_features), (optional, default=None)
            Right argument of the returned kernel k(X, Y). If None, k(X, X)
            if evaluated instead.

        eval_gradient : bool (optional, default=False)
            Determines whether the gradient with respect to the kernel
            hyperparameter is determined. Only supported when Y is None.

        active : np.ndarray (n_samples_X, n_features) (optional)
            Boolean array specifying which hyperparameters are active.

        Returns
        -------
        K : array, shape (n_samples_X, n_samples_Y)
            Kernel k(X, Y)

        K_gradient : array (opt.), shape (n_samples_X, n_samples_X, n_dims)
            The gradient of the kernel k(X, X) with respect to the
            hyperparameter of the kernel. Only returned when eval_gradient
            is True.
        """
        X = np.atleast_2d(X)
        if Y is None:
            Y = X
        elif eval_gradient:
            raise ValueError("Gradient can only be evaluated when Y is None.")

        K = np.full(
            (X.shape[0], Y.shape[0]),
            self.constant_value,
            dtype=np.array(self.constant_value).dtype,
        )
        if eval_gradient:
            if not self.hyperparameter_constant_value.fixed:
                return (
                    K,
                    np.full(
                        (X.shape[0], X.shape[0], 1),
                        self.constant_value,
                        dtype=np.array(self.constant_value).dtype,
                    ),
                )
            else:
                return K, np.empty((X.shape[0], X.shape[0], 0))
        else:
            return K