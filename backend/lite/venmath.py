# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

"""(Deterministic) Math SPs"""

import math
import numpy as np

from venture.lite.exception import VentureValueError
from venture.lite.sp import SPType
from venture.lite.sp_help import binaryNum
from venture.lite.sp_help import binaryNumInt
from venture.lite.sp_help import deterministic_psp
from venture.lite.sp_help import deterministic_typed
from venture.lite.sp_help import dispatching_psp
from venture.lite.sp_help import no_request
from venture.lite.sp_help import unaryNum
from venture.lite.sp_help import zero_gradient
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import T_logistic
from venture.lite.utils import d_log_logistic
from venture.lite.utils import d_logit_exp
from venture.lite.utils import exp
from venture.lite.utils import expm1
from venture.lite.utils import log
from venture.lite.utils import log1p
from venture.lite.utils import log_logistic
from venture.lite.utils import logistic
from venture.lite.utils import logit
from venture.lite.utils import logit_exp
from venture.lite.utils import logsumexp

import venture.lite.types as t
import venture.lite.value as v

def vvsum(venture_array):
  # TODO Why do the directions come in and out as Venture Values
  # instead of being unpacked by f_type.gradient_type()?
  return v.VentureNumber(sum(venture_array.getArray(t.NumberType())))

def symbolic_zero_left(n, obj):
  assert n == 0, "Cannot add non-zero integer %r to %r" % (n, obj)
  return obj

def symbolic_zero_right(obj, n):
  assert n == 0, "Cannot add non-zero integer %r to %r" % (n, obj)
  return obj

generic_add = dispatching_psp(
  [SPType([t.Int], t.Int, variadic=True),
   SPType([t.Int, t.Number], t.Number),
   SPType([t.Number, t.Int], t.Number),
   SPType([t.NumberType()], t.NumberType(), variadic=True),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType()),
          variadic=True),
   SPType([t.Int, t.Object], t.Object),
   SPType([t.Object, t.Int], t.Object),
   SPType([t.Object, t.Object], t.Object),
   ],
  [deterministic_psp(lambda *args: sum(args),
    sim_grad=lambda args, direction: [direction for _ in args],
    descr="add returns the sum of all its arguments"),
   deterministic_psp(lambda a, b: a + b),
   deterministic_psp(lambda a, b: a + b),
   deterministic_psp(lambda *args: sum(args),
    sim_grad=lambda args, direction: [direction for _ in args],
    descr="add returns the sum of all its arguments"),
   deterministic_psp(np.add,
    sim_grad=lambda args, direction: [direction, vvsum(direction)]),
   deterministic_psp(np.add,
    sim_grad=lambda args, direction: [vvsum(direction), direction]),
   deterministic_psp(lambda *args: np.sum(args, axis=0),
    sim_grad=lambda args, direction: [direction for _ in args],
    descr="add returns the sum of all its arguments"),
   deterministic_psp(symbolic_zero_left,
    sim_grad=lambda args, direction: [0, direction]),
   deterministic_psp(symbolic_zero_right,
    sim_grad=lambda args, direction: [direction, 0]),
   deterministic_psp(lambda a, b: a + b),
 ])

registerBuiltinSP("add", no_request(generic_add))

generic_sub = dispatching_psp(
  [SPType([t.NumberType(), t.NumberType()], t.NumberType()),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()),
           t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType()))],
  [deterministic_psp(lambda x, y: x - y,
    sim_grad=lambda args, direction: [direction, -direction],
    descr="sub returns the difference between its first and second arguments"),
   deterministic_psp(np.subtract,
    sim_grad=lambda args, direction: [direction, -vvsum(direction)]),
   deterministic_psp(np.subtract,
    sim_grad=lambda args, direction: [vvsum(direction), -direction]),
   deterministic_psp(np.subtract,
    sim_grad=lambda args, direction: [direction, -direction],
    descr="sub returns the difference between its first and second arguments")])

registerBuiltinSP("sub", no_request(generic_sub))

def grad_times(args, direction):
  assert len(args) == 2, "Gradient only available for binary multiply"
  return [direction*args[1], direction*args[0]]

def grad_scalar_times_vector(args, direction):
  dot_prod = v.vv_dot_product(v.VentureArrayUnboxed(args[1], t.NumberType()),
                              direction)
  return [ v.VentureNumber(dot_prod), direction * args[0] ]

def grad_vector_times_scalar(args, direction):
  dot_prod = v.vv_dot_product(v.VentureArrayUnboxed(args[0], t.NumberType()),
                              direction)
  return [ direction * args[1], v.VentureNumber(dot_prod) ]

generic_times = dispatching_psp(
  [SPType([t.NumberType()], t.NumberType(), variadic=True),
   SPType([t.NumberType(), t.ArrayUnboxedType(t.NumberType())],
          t.ArrayUnboxedType(t.NumberType())),
   SPType([t.ArrayUnboxedType(t.NumberType()), t.NumberType()],
          t.ArrayUnboxedType(t.NumberType()))],
  [deterministic_psp(lambda *args: reduce(lambda x,y: x * y,args,1),
    sim_grad=grad_times,
    descr="mul returns the product of all its arguments"),
   deterministic_psp(np.multiply,
    sim_grad=grad_scalar_times_vector, descr="scalar times vector"),
   deterministic_psp(np.multiply,
    sim_grad=grad_vector_times_scalar, descr="vector times scalar")])

registerBuiltinSP("mul", no_request(generic_times))

def divide(x, y):
  if y == 0:
    if x > 0:
      return float('+inf')
    elif x < 0:
      return float('-inf')
    else:
      return float('NaN')
  else:
    return x / y

def grad_div(args, direction):
  return [direction * (1 / args[1]),
          direction * (- args[0] / (args[1] * args[1]))]

registerBuiltinSP("div", binaryNum(divide,
    sim_grad=grad_div,
    descr="div returns the ratio of its first argument to its second") )

def integer_divide(x, y):
  if int(y) == 0:
    raise VentureValueError("division by zero")
  else:
    return int(x) // int(y)

registerBuiltinSP("int_div", binaryNumInt(integer_divide,
    descr="int_div(n, d) = floor(n/d)"))

def integer_mod(x, y):
  if int(y) == 0:
    raise VentureValueError("modulo by zero")
  else:
    return int(x) % int(y)

registerBuiltinSP("int_mod", binaryNumInt(integer_mod,
    descr="int_mod(n, d) = r, where n = d*q + r and q = floor(n/d)"))

registerBuiltinSP("min",
    binaryNum(min, descr="min returns the minimum value of its arguments"))
registerBuiltinSP("max",
    binaryNum(max, descr="max returns the maximum value of its arguments"))

registerBuiltinSP("floor", unaryNum(math.floor,
    sim_grad=zero_gradient,
    descr="floor returns the largest integer less than or equal to its " \
          "argument (as a VentureNumber)") )

def grad_sin(args, direction):
  return [direction * math.cos(args[0])]

registerBuiltinSP("sin", unaryNum(math.sin, sim_grad=grad_sin,
    descr="Returns the sin of its argument"))

def grad_cos(args, direction):
  return [-direction * math.sin(args[0])]

registerBuiltinSP("cos", unaryNum(math.cos, sim_grad=grad_cos,
    descr="Returns the cos of its argument"))

def grad_tan(args, direction):
  return [direction * math.pow(math.cos(args[0]), -2)]

registerBuiltinSP("tan", unaryNum(math.tan, sim_grad=grad_tan,
    descr="Returns the tan of its argument"))

registerBuiltinSP("hypot", binaryNum(math.hypot,
    descr="Returns the hypot of its arguments"))

registerBuiltinSP("exp", unaryNum(exp,
    sim_grad=lambda args, direction: [direction * exp(args[0])],
    descr="Returns the exp of its argument"))

registerBuiltinSP("expm1", unaryNum(expm1,
    sim_grad=lambda args, direction: [direction * exp(args[0])],
    descr="Returns the exp of its argument, minus one"))

registerBuiltinSP("log", unaryNum(log,
    sim_grad=lambda args, direction: [direction * (1 / float(args[0]))],
    descr="Returns the log of its argument"))

registerBuiltinSP("log1p", unaryNum(log1p,
    sim_grad=lambda args, direction: [direction * (1 / (1 + float(args[0])))],
    descr="Returns the log of one plus its argument"))

def grad_pow(args, direction):
  x, y = args
  # Use np.log so we get NaN rather than exception in the case of
  # computing d x^y = x^y (log x dy + y/x dx) at x < 0 but we never
  # use the dy component later.
  return [direction * y * math.pow(x, y - 1),
          direction * np.log(x) * math.pow(x, y)]

registerBuiltinSP("pow", binaryNum(math.pow, sim_grad=grad_pow,
    descr="pow returns its first argument raised to the power " \
          "of its second argument"))

def grad_sqrt(args, direction):
  return [direction * (0.5 / math.sqrt(args[0]))]

registerBuiltinSP("sqrt", unaryNum(math.sqrt, sim_grad=grad_sqrt,
    descr="Returns the sqrt of its argument"))

def grad_atan2(args, direction):
  (y,x) = args
  denom = x*x + y*y
  return [direction * (x / denom), direction * (-y / denom)]

registerBuiltinSP("atan2", binaryNum(math.atan2,
    sim_grad=grad_atan2,
    descr="atan2(y,x) returns the angle from the positive x axis "\
          "to the point x,y.  The order of arguments is conventional."))

def grad_negate(_args, direction):
  return [-direction]

registerBuiltinSP("negate", unaryNum(lambda x: -x, sim_grad=grad_negate,
    descr="negate(x) returns -x, the additive inverse of x."))

def signum(x):
  if x == 0:
    return 0
  else:
    return x/abs(x)

def grad_abs(args, direction):
  # XXX discontinuity?
  [x] = args
  return [direction * signum(x)]

registerBuiltinSP("abs", unaryNum(abs, sim_grad=grad_abs,
    descr="abs(x) returns the absolute value of x."))

registerBuiltinSP("signum", unaryNum(signum,
    descr="signum(x) returns the sign of x " \
          "(1 if positive, -1 if negative, 0 if zero)."))

def grad_logistic(args, direction):
  [x] = args
  (_, deriv) = T_logistic(x)
  return [direction * deriv]

registerBuiltinSP("logistic", unaryNum(logistic, sim_grad=grad_logistic,
    descr="The logistic function: 1/(1+exp(-x))"))

def grad_logisticv(args, direction):
  # XXX The direction is a Venture value, but the deriv is a Python
  # (numpy) array :(
  [x] = args
  (_, deriv) = T_logistic(x)
  answer = direction.array * deriv
  # print "Gradient of logistic got", x, deriv, direction.array, answer
  return [v.VentureArrayUnboxed(answer, t.Number)]

registerBuiltinSP("logisticv", deterministic_typed(logistic,
    [t.UArray(t.Number)], t.UArray(t.Number),
    sim_grad=grad_logisticv,
    descr="The logistic function: 1/(1+exp(-x))"))

registerBuiltinSP("logit", unaryNum(logit,
    descr="The logit (inverse logistic) function: log(x/(1-x))"))

def grad_log_logistic(args, direction):
  [x] = args
  return [direction * d_log_logistic(x)]

registerBuiltinSP("log_logistic", unaryNum(log_logistic,
    sim_grad=grad_log_logistic,
    descr="The log of the logistic function: -log (1 + exp(-x))"))

def grad_logit_exp(args, direction):
  [x] = args
  return [direction * d_logit_exp(x)]

registerBuiltinSP("logit_exp", unaryNum(logit_exp,
    sim_grad=grad_logit_exp,
    descr="The logit of exp: -log (exp(-x) - 1)"))

registerBuiltinSP("logsumexp", deterministic_typed(logsumexp,
    [t.UArray(t.Number)], t.Number,
    descr="Equivalent to log(apply(add, mapv(exp, x)))"))
