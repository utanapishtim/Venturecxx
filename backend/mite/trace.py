from venture.lite.address import Address
from venture.lite.address import List
from venture.lite.env import VentureEnvironment
from venture.lite.node import OutputNode
from venture.lite.trace import Trace as LiteTrace

from venture.mite.builtin import builtInSPs
from venture.mite.builtin import builtInValues
from venture.mite.evaluator import evalFamily, unevalFamily, processMadeSP
from venture.mite.sp import Args

class Trace(LiteTrace):
  def __init__(self):
    self.globalEnv = VentureEnvironment()
    for name, val in builtInValues().iteritems():
      self.bindPrimitiveName(name, val)
    for name, sp in builtInSPs().iteritems():
      self.bindPrimitiveSP(name, sp)
    self.sealEnvironment() # New frame so users can shadow globals

    self.unpropagatedObservations = {}
    self.families = {}

  def bindPrimitiveSP(self, name, sp):
    spNode = self.createConstantNode(None, sp)
    processMadeSP(self, spNode)
    self.globalEnv.addBinding(name, spNode)

  def createApplicationNodes(self, address, operatorNode, operandNodes, env):
    # Request nodes don't exist now, so just create a singular node.
    outputNode = OutputNode(address, operatorNode, operandNodes, None, env)
    self.addChildAt(operatorNode, outputNode)
    for operandNode in operandNodes:
      self.addChildAt(operandNode, outputNode)
    return outputNode

  def argsAt(self, node):
    return Args(self, node)

  def madeSPAt(self, node):
    # SPs and SPRecords are the same now.
    return self.madeSPRecordAt(node)

  def eval(self, id, exp):
    assert id not in self.families
    (_, self.families[id]) = evalFamily(
      self, Address(List(id)), self.unboxExpression(exp), self.globalEnv)

  def uneval(self, id):
    assert id in self.families
    unevalFamily(self, self.families[id])
    del self.families[id]

  def makeConsistent(self):
    for node, val in self.unpropagatedObservations.iteritems():
      print 'propagate', node, val
    self.unpropagatedObservations.clear()
    return 0

  def primitive_infer(self, exp):
    print 'primitive_infer', exp
    return None

  def select(self, scope, block):
    print 'select', scope, block
    return None

  def just_detach(self, scaffold):
    print 'detach', scaffold
    return 0, None

  def just_regen(self, scaffold):
    print 'regen', scaffold
    return 0

  def just_restore(self, scaffold, rhoDB):
    print 'restore', scaffold, rhoDB
    return 0