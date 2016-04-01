import numbers

from venture.exception import VentureException
from venture.lite.exception import VentureError
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.value import SPRef
import venture.lite.exp as e

from venture.mite.sp import VentureSP

## evaluation

def evalFamily(trace, address, exp, env):
  weight = 0
  if e.isVariable(exp):
    try:
      sourceNode = env.findSymbol(exp)
    except VentureError as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address), \
        None, info[2]
    # weight = regen(trace, sourceNode, scaffold,
    #                shouldRestore, omegaDB, gradients)
    return (weight, trace.createLookupNode(address, sourceNode))
  elif e.isSelfEvaluating(exp):
    return (0, trace.createConstantNode(address, exp))
  elif e.isQuotation(exp):
    return (0, trace.createConstantNode(address, e.textOfQuotation(exp)))
  else:
    weight = 0
    nodes = []
    for index, subexp in enumerate(exp):
      addr = address.extend(index)
      w, n = evalFamily(trace, addr, subexp, env)
      weight += w
      nodes.append(n)
    outputNode = trace.createApplicationNodes(address, nodes[0], nodes[1:], env)
    try:
      weight += apply(trace, outputNode)
    except VentureException:
      raise # Avoid rewrapping with the below
    except Exception as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address,
                             cause=err), None, info[2]
    assert isinstance(weight, numbers.Number)
    return weight, outputNode

def apply(trace, node):
  sp = trace.spAt(node)
  args = trace.argsAt(node)
  assert isinstance(sp, VentureSP)

  # if omegaDB.hasValueFor(node): oldValue = omegaDB.getValue(node)
  # else: oldValue = None

  weight = 0
  # if scaffold.hasLKernel(node):
  # else:
  newValue = sp.apply(args) # if not shouldRestore else oldValue

  trace.setValueAt(node, newValue)
  if isinstance(newValue, VentureSP):
    processMadeSP(trace, node)
  # if sp.isRandom(): trace.registerRandomChoice(node)
  # if isTagOutputPSP(psp):
  assert isinstance(weight, numbers.Number)
  return weight

def processMadeSP(trace, node):
  sp = trace.valueAt(node)
  assert isinstance(sp, VentureSP)
  # if isAAA:
  #   trace.discardAAAMadeSPAuxAt(node)
  # if sp.hasAEKernel(): trace.registerAEKernel(node)
  trace.setMadeSPRecordAt(node, sp)
  trace.setValueAt(node, SPRef(node))

## unevaluation

def unevalFamily(trace, node):
  weight = 0
  if isConstantNode(node): pass
  elif isLookupNode(node):
    assert len(trace.parentsAt(node)) == 1
    trace.disconnectLookup(node)
    trace.setValueAt(node, None)
    # weight += extractParents(trace, node, scaffold, omegaDB, compute_gradient)
  else:
    assert isOutputNode(node)
    weight += unapply(trace, node)
    for operandNode in reversed(node.operandNodes):
      weight += unevalFamily(trace, operandNode)
    weight += unevalFamily(trace, node.operatorNode)
  return weight

def unapply(trace, node):
  sp = trace.spAt(node)
  args = trace.argsAt(node)
  # if isTagOutputPSP(psp):
  # if sp.isRandom(): trace.registerRandomChoice(node)
  value = trace.valueAt(node)
  if (isinstance(value, SPRef) and value.makerNode is node):
    teardownMadeSP(trace, node)

  weight = 0
  # if scaffold.hasLKernel(node):
  # else:
  sp.unapply(args)
  # omegaDB.extractValue(node,trace.valueAt(node))

  trace.setValueAt(node, None)
  # if compute_gradient:
  return weight

def teardownMadeSP(trace, node):
  sp = trace.madeSPRecordAt(node)
  assert isinstance(sp, VentureSP)
  # assert len(spRecord.spFamilies.families) == 0
  trace.setValueAt(node, sp)
  # if sp.hasAEKernel(): trace.unregisterAEKernel(node)
  # if isAAA:
  #   trace.registerAAAMadeSPAuxAt(node,trace.madeSPAuxAt(node))
  trace.setMadeSPRecordAt(node, None)