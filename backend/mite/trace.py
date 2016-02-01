from venture.lite.trace import *
from venture.lite.discrete import *

from venture.mite.sp import *
from venture.mite.csp import *
from venture.mite.eval import *

LiteTrace = Trace
class Trace(LiteTrace):
    def __init__(self):
        self.globalEnv = VentureEnvironment()
        self.families = {}
        self.unpropagatedObservations = {}

        self.bindPrimitiveSP('beta', SimpleRandomSPWrapper(builtInSPs()['beta'].outputPSP))
        self.bindPrimitiveSP('flip', SimpleRandomSPWrapper(builtInSPs()['flip'].outputPSP))
        self.bindPrimitiveSP('add', SimpleDeterministicSPWrapper(builtInSPs()['add'].outputPSP))
        coin = SimpleRandomSPWrapper(
            TypedPSP(CBetaBernoulliOutputPSP(1.0, 1.0),
                     SPType([], t.BoolType())))
        coin.constructSPAux = BetaBernoulliSPAux
        self.bindPrimitiveSP('coin', coin)

        self.bindPrimitiveSP('make_csp', SimpleDeterministicSPWrapper(make_csp))

    def extractValue(self, id):
        return self.boxValue(self.extractRaw(id))

    def extractRaw(self,id): return self.valueAt(self.families[id])

    def eval(self, id, exp):
        assert id not in self.families
        (_, family) = evalFamily(self, Address(List(id)), self.unboxExpression(exp), self.globalEnv)
        self.families[id] = family

    def uneval(self, id):
        assert id in self.families
        unevalFamily(self, self.families[id])
        del self.families[id]

    def bindInGlobalEnv(self, sym, id):
        try:
            self.globalEnv.addBinding(sym,self.families[id])
        except VentureError as e:
            raise VentureException("invalid_argument", message=e.message, argument="symbol")

    def observe(self, id, val):
        node = self.families[id]
        self.unpropagatedObservations[node] = self.unboxValue(val)

    def makeConsistent(self):
        weight = 0
        for node, val in self.unpropagatedObservations.iteritems():
            # TODO do this with regen to deal with propagation and references and stuff
            appNode = self.getConstrainableNode(node)
            node.observe(val)
            weight += constrain(self, appNode, node.observedValue)
        self.unpropagatedObservations.clear()
        return weight

    # this will hopefully become unnecessary, but will do for now
    def getConstrainableNode(self, node):
        if isLookupNode(node): return self.getConstrainableNode(node.sourceNode)
        return node

    def unobserve(self, id):
        node = self.families[id]
        appNode = self.getConstrainableNode(node)
        if node.isObservation:
            unconstrain(self, appNode, node.observedValue)
            node.isObservation = False
        else:
            assert node in self.unpropagatedObservations
            del self.unpropagatedObservations[node]

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

    # modified from lite trace due to request node change
    def createOutputNode(self,address,operatorNode,operandNodes,env):
        outputNode = OutputNode(address,operatorNode,operandNodes,[],env)
        self.addChildAt(operatorNode,outputNode)
        for operandNode in operandNodes:
            self.addChildAt(operandNode,outputNode)
        return outputNode

    def createRequestNode(self,address,operatorNode,operandNodes,outputNode,env):
        # TODO: compute more precise edges between request node and operands
        # and add ESR edges to downstream request nodes
        # also, should probably make subclasses for RequestNode and OutputNode
        # more precisely:
        # output node should maintain a set of requests and operands that it currently depends on
        # request node should copy this set and create child edges to it
        # any requests made should be added to the output node's set
        # when the output node is finalized, add any additional ESR edges.
        # note that addESREdge increments the ref count, which we only want to do once.
        # also, when popping a request, copy its parent set to the output node (discarding the output node's current set)
        # it will be copied back over when re-evaluating.
        requestNode = RequestNode(address,operatorNode,operandNodes,env)
        self.addChildAt(operatorNode,requestNode)
        for operandNode in operandNodes:
            self.addChildAt(operandNode,requestNode)
        requestNode.registerOutputNode(outputNode)
        outputNode.requestNode.append(requestNode)
        return requestNode

    def removeRequestNode(self,requestNode):
        self.removeChildAt(requestNode.operatorNode, requestNode)
        for operandNode in requestNode.operandNodes:
            self.removeChildAt(operandNode, requestNode)

    def allocateRequestNode(self, node, request, env):
        if not hasattr(node, 'requestStack'):
            node.requestStack = []
        if node.requestStack:
            requestNode = node.requestStack.pop()
            oldRequest = self.valueAt(requestNode)
            assert all(esr.id == old.id for esr, old in zip(request.esrs, oldRequest.esrs))
            return requestNode, False
        else:
            requestNode = self.createRequestNode(
                node.address, node.operatorNode, node.operandNodes, node, env)
            self.setValueAt(requestNode, request)
            return requestNode, True

    def freeRequestNode(self, node, request, env):
        # TODO: check if the request node was identified as brush,
        # and if not, put it on the stack instead of blowing it away
        # need to get a scaffold here somehow...
        requestNode = node.requestNode.pop()
        oldRequest = self.valueAt(requestNode)
        assert all(esr.id == old.id for esr, old in zip(request.esrs, oldRequest.esrs))
        if False:
            node.requestStack.append(requestNode)
            return requestNode, False
        else:
            return requestNode, True

    # modified to return our own Args object
    def argsAt(self, node): return Args(self, node)

LiteArgs = Args
class Args(LiteArgs):
    def requestValues(self, request):
        requestNode, created = self.trace.allocateRequestNode(self.node, request, self.env)
        weight = 0
        if created:
            weight += evalRequests(self.trace, requestNode)
        values = self.esrValues()
        return values, weight

    def requestFree(self, request):
        requestNode, deleted = self.trace.freeRequestNode(self.node, request, self.env)
        weight = 0
        if deleted:
            weight += unevalRequests(self.trace, requestNode)
        return weight