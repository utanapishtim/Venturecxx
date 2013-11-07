#include "value.h"
#include "node.h"
#include "env.h"
#include "pytrace.h"
#include "infer/gkernel.h"
#include "infer/mh.h"
#include "infer/gibbs.h"
#include "infer/pgibbs.h"
#include "infer/meanfield.h"
#include "value.h"
#include "scaffold.h"

#include <iostream>
#include <list>

using boost::python::extract;

PyTrace::PyTrace(): 
  Trace(),
//  mcmc(new OutermostMixMH(this, new ScaffoldMHGKernel(this))) {}
//  mcmc(new OutermostMixMH(this,new GibbsGKernel(this))) {}
  mcmc(new OutermostMixMH(this,new PGibbsGKernel(this))) {}
//  mcmc(new OutermostMixMH(this,new MeanFieldGKernel(this))) {}


PyTrace::~PyTrace()
{
  OutermostMixMH * mKernel = dynamic_cast<OutermostMixMH*>(mcmc);
  delete mKernel->gKernel;
  delete mcmc;
}

VentureValue * PyTrace::parseValue(boost::python::dict d)
{
  if (d["type"] == "boolean") { return new VentureBool(extract<bool>(d["value"])); }
  else if (d["type"] == "number") { return new VentureNumber(extract<double>(d["value"])); }
  else if (d["type"] == "symbol") { return new VentureSymbol(extract<string>(d["value"])); }
  else if (d["type"] == "atom") { return new VentureAtom(extract<uint32_t>(d["value"])); }
  else { assert(false); }
}


VentureValue * PyTrace::parseExpression(boost::python::object o)
{
  extract<boost::python::dict> getDict(o);
  if (getDict.check()) { return parseValue(getDict()); }
  
  extract<boost::python::list> getList(o);
  assert(getList.check());
  
  boost::python::list l = getList();
  
 VentureList * exp = new VentureNil;
 
 boost::python::ssize_t L = boost::python::len(l);

 for(boost::python::ssize_t i=L;i > 0;i--) 
 {
   exp = new VenturePair(parseExpression(l[i-1]),exp);
 }
 return exp;
}

void PyTrace::evalExpression(size_t directiveID, boost::python::object o)
{
  VentureValue * exp = parseExpression(o);

  pair<double,Node*> p = evalVentureFamily(directiveID,static_cast<VentureList*>(exp),nullptr);
  ventureFamilies.insert({directiveID,{p.second,exp}});
}

boost::python::object PyTrace::extractPythonValue(size_t directiveID)
{
  Node * node;
  tie(node,ignore) = ventureFamilies[directiveID];
  assert(node);
  VentureValue * value = node->getValue();
  assert(value);
  return value->toPython();
}

void PyTrace::bindInGlobalEnv(string sym, size_t directiveID)
{
  globalEnv->addBinding(new VentureSymbol(sym),ventureFamilies[directiveID].first);
}

void PyTrace::observe(size_t directiveID,boost::python::object valueExp)
{
  Node * node;
  tie(node,ignore) = ventureFamilies[directiveID];
  VentureValue * val = parseExpression(valueExp);
  assert(!dynamic_cast<VenturePair*>(val));
  assert(!dynamic_cast<VentureSymbol*>(val));
  node->observedValue = val;
  constrain(node,true);
}

void PyTrace::infer(size_t n) 
{ 
  if (pgibbsWithGlobalScaffold)
  {
    for (size_t i = 0; i < n; i++)
    {
      set<Node *> allNodes(randomChoices.begin(),randomChoices.end());
//      ScaffoldMHGKernel * p = new ScaffoldMHGKernel(this);
      PGibbsGKernel * p = new PGibbsGKernel(this);
      p->loadParameters(new ScaffoldMHParam(new Scaffold(allNodes),nullptr));
      p->infer(1); 
      p->destroyParameters();
      delete p;
    }
  }
  else 
  {
    mcmc->infer(n);
  }
}

BOOST_PYTHON_MODULE(libtrace)
{
  using namespace boost::python;
  class_<PyTrace>("Trace",init<>())
    .def("eval", &PyTrace::evalExpression)
    .def("extractValue", &PyTrace::extractPythonValue)
    .def("bindInGlobalEnv", &PyTrace::bindInGlobalEnv)
    .def("observe", &PyTrace::observe)
    .def("infer", &PyTrace::infer)
    ;
};

