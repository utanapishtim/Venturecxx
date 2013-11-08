#include "builtin.h"

#include "sps/number.h"
#include "sps/bool.h"
#include "sps/continuous.h"
#include "sps/discrete.h"
#include "sps/csp.h"
#include "sps/mem.h"
#include "sps/cond.h"
#include "sps/eval.h"
#include "sps/envs.h"
#include "sps/pycrp.h"

#include "sps/makesymdirmult.h"
#include "sps/makeucsymdirmult.h"
#include "sps/makelazyhmm.h"

#include "sps/vector.h"
#include "sps/list.h"
#include "sps/map.h"

/* GC All new calls in both of these functions will be freed
   by Trace's destructor. */
map<string,VentureValue *> initBuiltInValues()
{
  return 
  { 
    {"true",new VentureBool(true)},
    {"false",new VentureBool(false)}
  };
}

map<string,SP *> initBuiltInSPs()
{
  return
  {
    // numbers
    {"plus", new PlusSP},
    {"minus", new MinusSP},
    {"times", new TimesSP},
    {"div", new DivideSP},
    {"power", new PowerSP},
    {"eq", new EqualSP},
    {"gt", new GreaterThanSP},
    {"lt", new LessThanSP},
    {"gte", new GreaterThanOrEqualToSP},
    {"lte", new LessThanOrEqualToSP},
    {"real", new RealSP},
    {"atom_eq", new AtomEqualSP},

    // lists
    {"pair", new PairSP},
    {"first", new FirstSP},
    {"rest", new RestSP},
    {"list", new ListSP},
    {"is_pair", new IsPairSP},
    {"list_ref", new ListRefSP},
    {"map_list", new MapListSP},

    // vectors
    {"make_vector", new MakeVectorSP},
    {"vector_lookup", new VectorLookupSP},

    // maps
    {"make_map", new MakeMapSP},
    {"map_lookup", new MapLookupSP},
    
    // booleans
    {"and", new BoolAndSP},
    {"or", new BoolOrSP},
    {"not", new BoolNotSP},
    {"xor", new BoolXorSP},

    // discrete distributions
    {"flip", new BernoulliSP},
    {"bernoulli", new BernoulliSP},
    {"categorical", new CategoricalSP},
    {"uniform_discrete", new UniformDiscreteSP},

    // continuous distributions
    {"normal", new NormalSP},
    {"gamma", new GammaSP},
    {"uniform_continuous", new UniformContinuousSP},
    {"beta", new BetaSP},
    {"student_t", new StudentTSP},

    // control flow
    {"branch", new BranchSP},
    {"biplex", new BiplexSP},

    // environments
    {"get_current_environment", new GetCurrentEnvSP},
    {"get_empty_environment", new GetEmptyEnvSP},
    {"extend_environment", new ExtendEnvSP},
    {"eval", new EvalSP},

    // exchangeable random procedures
    {"make_sym_dir_mult", new MakeSymDirMultSP},
    {"make_uc_sym_dir_mult", new MakeUCSymDirMultSP},

    {"make_crp", new MakePitmanYorCRPSP},

    // miscellaneous?
    {"make_lazy_hmm", new MakeLazyHMMSP},

    {"mem", new MSPMakerSP},
  };
}

