#ifndef NUMBER_SPS_H
#define NUMBER_SPS_H

#include "sp.h"

/* Deterministic Real SPs. */
struct PlusSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct MinusSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct TimesSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct DivideSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct PowerSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct EqualSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct GreaterThanSP : SP
{
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct LessThanSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct GreaterThanOrEqualToSP : SP
{
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct LessThanOrEqualToSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct RealSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct IntPlusSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct IntMinusSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct IntTimesSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct IntDivideSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct IntEqualSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct AtomEqualSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

#endif
