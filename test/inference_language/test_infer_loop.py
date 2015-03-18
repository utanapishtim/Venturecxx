from nose.tools import eq_
import time
import threading

from venture.test.config import get_ripl, on_inf_prim

@on_inf_prim("none")
def testStopSmoke():
  get_ripl().stop_continuous_inference()

def assertInferring(ripl):
  # If continuous inference is really running, the value of x should
  # change without me doing anything
  v = ripl.sample("x")
  time.sleep(0.00001) # Yield to give CI a chance to work
  assert not v == ripl.sample("x")

def assertNotInferring(ripl):
  # If not running continuous inference, sampling the same variable
  # always gives the same answer.
  v = ripl.sample("x")
  time.sleep(0.00001) # Yield to give CI a chance to work, if it's on
  assert v == ripl.sample("x")

@on_inf_prim("mh") # Really loop, but that's very special
def testInferLoopSmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")

  assertNotInferring(ripl)

  try:
    ripl.infer("(loop ((mh default one 1)))")
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("mh") # Really loop, but that's very special
def testStartStopInferLoop():
  numthreads = threading.active_count()
  ripl = get_ripl()
  eq_(numthreads, threading.active_count())
  ripl.assume("x", "(normal 0 1)")
  assertNotInferring(ripl)
  eq_(numthreads, threading.active_count())
  try:
    ripl.infer("(loop ((mh default one 1)))")
    assertInferring(ripl)
    eq_(numthreads+1, threading.active_count())
    with ripl.sivm._pause_continuous_inference():
      assertNotInferring(ripl)
      eq_(numthreads, threading.active_count())
    assertInferring(ripl)
    eq_(numthreads+1, threading.active_count())
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("mh") # Really loop, but that's very special
def testStartCISmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")

  assertNotInferring(ripl)

  try:
    ripl.start_continuous_inference("(mh default one 1)")
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around

@on_inf_prim("mh") # Really loop, but that's very special
def testStartCIInstructionSmoke():
  ripl = get_ripl()
  ripl.assume("x", "(normal 0 1)")

  assertNotInferring(ripl)

  try:
    ripl.execute_instruction("[start_continuous_inference (mh default one 1)]")
    assertInferring(ripl)
  finally:
    ripl.stop_continuous_inference() # Don't want to leave active threads lying around
