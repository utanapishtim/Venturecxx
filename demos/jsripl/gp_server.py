# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

import numpy as np
import numpy.linalg as la
import numpy.random as npr
import scipy.spatial.distance

def const(c):
  def f(x1, x2):
    return c
  return f

def isotropic_covariance(f):
  def k(x1, x2):
    r2 = scipy.spatial.distance.cdist([[x1]], [[x2]], 'sqeuclidean')
    return f(r2[0][0])
  return k

delta = isotropic_covariance(lambda r: 1.*(r == 0))

def dotproduct_covariance(f, origin):
  def k(x1, x2):
    return f(np.outer(x1 - origin, x2 - origin)[0][0])
  return k

def linear(v, c):
  def f(p):
    return v*p
  return dotproduct_covariance(f, c)

def squared_exponential(a, l):
  def f(r2):
    return a * np.exp(-r2/l**2)
  return isotropic_covariance(f)

def lift_binary(op):
  def lifted(f1, f2):
    return lambda *xs: op(f1(*xs), f2(*xs))
  return lifted

from venture import shortcuts as s
ripl = s.make_lite_church_prime_ripl()

from venture.lite.function import VentureFunction
from venture.lite.sp import SPType
import venture.lite.value as v
import venture.lite.types as t
import venture.value.dicts as d

fType = t.AnyType("VentureFunction")

# input and output types for gp
xType = t.NumberType()
oType = t.NumberType()
kernelType = SPType([xType, xType], oType)

ripl.assume('app', 'apply_function')

constantType = SPType([t.AnyType()], oType)
def makeConstFunc(c):
  return VentureFunction(lambda _: c, sp_type=constantType)

ripl.assume('make_const_func', VentureFunction(makeConstFunc, [xType], constantType))

#ripl.assume('zero', "(app make_const_func 0)")
#print ripl.predict('(app zero 1)')

def makeSquaredExponential(a, l):
  return VentureFunction(squared_exponential(a, l), sp_type=kernelType)

ripl.assume('make_squared_exponential', VentureFunction(makeSquaredExponential, [t.NumberType(), xType], fType))

#ripl.assume('sq_exp', '(app make_squared_exponential 1 1)')
#print ripl.predict('(app sq_exp 0 1)')

def makeLinear(v, c):
  return VentureFunction(linear(v, c), sp_type=kernelType)

ripl.assume('make_linear', VentureFunction(makeLinear, [t.NumberType(), xType], fType))
#ripl.assume('linear', '(app make_linear 1 1)')
#print ripl.predict('(app linear 2 3)')

liftedBinaryType = SPType([t.AnyType(), t.AnyType()], t.AnyType())

def makeLiftedBinary(op):
  lifted_op = lift_binary(op)
  def wrapped(f1, f2):
    sp_type = f1.sp_type
    assert(f2.sp_type == sp_type)
    return VentureFunction(lifted_op(f1, f2), sp_type=sp_type)
  return VentureFunction(wrapped, sp_type=liftedBinaryType)

ripl.assume("func_plus", makeLiftedBinary(lambda x1, x2: x1+x2))
#print ripl.predict('(app (app func_plus sq_exp sq_exp) 0 1)')
ripl.assume("func_times", makeLiftedBinary(lambda x1, x2: x1*x2))

program = """
  [assume mu (normal 0 5)]
  [assume mean (app make_const_func mu)]

;  [assume a (inv_gamma 2 5)]
  [assume a 1]
;  [assume l (inv_gamma 5 50)]
;  [assume l (uniform_continuous 10 100)]
  [assume l 10]

;  [assume cov (app (if (flip) func_plus func_times) (app make_squared_exponential a l) (app make_linear 1 (normal 0 10)))]
  
;  [assume noise (inv_gamma 3 1)]
  [assume noise 0.1]
  [assume noise_func (app make_squared_exponential noise 0.1)]
  
  [assume is_linear (flip)]
  [assume cov 
    (app func_plus noise_func
      (if is_linear
        (app make_linear 1 (normal 0 10))
        (app make_squared_exponential a l)))]

;  [assume cov (app make_linear a 0)]
  
  gp : [assume gp (make_gp mean cov)]
  
  [assume obs_fn (lambda (obs_id x) (gp x))]
;  [assume obs_fn (lambda (obs_id x) (normal x 1))]
"""

ripl.execute_program(program)

samples = [
  (0, 1),
  (2, 3),
  (-4, 5),
]

def array(xs):
  return v.VentureArrayUnboxed(np.array(xs), xType)

xs, os = zip(*samples)

#ripl.observe(['gp', array(xs)], array(os))
ripl.infer("(incorporate)")

from venture.server import RiplRestServer

server = RiplRestServer(ripl)
server.run(host='127.0.0.1', port=8082)

