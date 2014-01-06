from psp import PSP
from request import Request,ESR

class BranchRequestPSP(PSP):
  def simulate(self,args): 
#    print "branchRequest::simulate()"
    assert not args.operandValues[0] is None
    if args.operandValues[0]: expIndex = 1
    else: expIndex = 2

    exp = args.operandValues[expIndex]
    return Request([ESR(args.node,exp,args.env)])

class BiplexOutputPSP(PSP):
  def simulate(self,args):
    if args.operandValues[0]:
      return args.operandValues[1]
    else:
      return args.operandValues[2]
