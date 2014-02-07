from abc import ABCMeta

class VentureValue(object):
  __metaclass__ = ABCMeta

  def getNumber(self): raise Exception("Cannot convert %s to number" % type(self))
  def getAtom(self): raise Exception("Cannot convert %s to atom" % type(self))
  def getBool(self): raise Exception("Cannot convert %s to bool" % type(self))
  def getSymbol(self): raise Exception("Cannot convert %s to symbol" % type(self))
  def getArray(self): raise Exception("Cannot convert %s to array" % type(self))
  def getPair(self): raise Exception("Cannot convert %s to pair" % type(self))
  def getSimplex(self): raise Exception("Cannot convert %s to simplex" % type(self))
  def getDict(self): raise Exception("Cannot convert %s to dict" % type(self))
  def getMatrix(self): raise Exception("Cannot convert %s to matrix" % type(self))
  def getSP(self): raise Exception("Cannot convert %s to sp" % type(self))
  def getEnvironment(self): raise Exception("Cannot convert %s to environment" % type(self))

class VentureNumber(VentureValue):
  def __init__(self,number): self.number = number
  def getNumber(self): return self.number

class VentureAtom(VentureValue):
  def __init__(self,atom): self.atom = atom
  def getNumber(self): return self.atom
  def getBool(self): return self.atom

class VentureBool(VentureValue):
  def __init__(self,boolean): self.boolean = boolean
  def getBool(self): return self.boolean

class VentureSymbol(VentureValue):
  def __init__(self,symbol): self.symbol = symbol
  def getSymbol(self): return self.symbol

class VentureArray(VentureValue):
  def __init__(self,array): self.array = array
  def getArray(self): return self.array

class VentureNil(VentureValue):
  def __init__(self): pass

class VenturePair(VentureValue):
  def __init__(self,first,rest):
    self.first = first
    self.rest = rest
  def getPair(self): return (self.first,self.rest)

class VentureSimplex(VentureValue):
  def __init__(self,simplex): self.simplex = simplex
  def getSimplex(self): return self.simplex

class VentureDict(VentureValue):
  def __init__(self,d): self.dict = d
  def getDict(self): return self.dict

class VentureMatrix(VentureValue):
  def __init__(self,matrix): self.matrix = matrix
  def getMatrix(self): return self.matrix

class SPRef(VentureValue):
  def __init__(self,makerNode): self.makerNode = makerNode

## SPs and Environments as well
