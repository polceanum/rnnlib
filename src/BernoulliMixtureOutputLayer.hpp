/*Copyright 2009,2010 Alex Graves
  2014 Sergey Zyrianov

 This file is part of RNNLIB.

 RNNLIB is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 RNNLIB is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with RNNLIB.  If not, see <http://www.gnu.org/licenses/>.*/

#ifndef rnnlib_xcode_BernoulliMixtureOutputLayer_hpp
#define rnnlib_xcode_BernoulliMixtureOutputLayer_hpp
#include "SoftmaxLayer.hpp"
#include "Random.hpp"
#include "BivariateNorm.h"
#include <boost/math/constants/constants.hpp>

struct BernoulliMixtureOutputLayer : public NetworkOutput, public FlatLayer {
  static const size_t plotSize = 100; // Size of output image corresponds to output neurons

  ostream &out;

  SeqBuffer<real_t> outputVariables;

  BernoulliMixtureOutputLayer(ostream &o,
                              const string &name)
      : FlatLayer(name, 1,
                  plotSize),
        out(o),
        outputVariables(plotSize) {
    criteria += "loss";
  }

  void start_sequence() {
    FlatLayer::start_sequence();
    outputVariables.reshape(outputActivations);
  }

  void feed_forward(const vector<int> &coords) {
    real_t *act = this->inputActivations[coords].begin();
    real_t *var = this->outputVariables[coords].begin();

    // Just apply sigmoid function to each output
    for(size_t idx = 0; idx < this->inputActivations[coords].size(); ++idx) {
        *var = Logistic::fn(-(*act));
        ++var;
        ++act;
    }
  }

  void feed_back(const vector<int> &coords) {

  }

  real_t calculate_errors(const DataSequence &seq) {
    Log<real_t> loss(0, true);

    LOOP(int pt, span(seq.inputs.seq_size() - 1)) {
      const real_t *target_t = seq.targetPatterns[pt].begin();

      real_t *output = this->outputVariables[pt].begin();

      for(size_t idx = 0; idx < this->outputVariables[pt].size(); ++idx) {
          real_t eosProb = *target_t ? *output
                                     : 1. - *output;
          loss *= Log<real_t>(eosProb);
          ++output;
          ++target_t;
      }

      partial_derivs(pt, target_t);
      if (!runningGradTest) {
        bound_range(inputErrors[pt], -100.0, 100.0);
      }
    }
    errorMap["loss"] = -loss.log();
    return -loss.log();
  }

  void partial_derivs(int pt,
                      const real_t *target_t) {
    View<real_t> intpuErrors_t = inputErrors[pt];
    View<real_t> outputVariables_t = outputVariables[pt];

    for(size_t idx = 0; idx < intpuErrors_t.size(); ++idx) {
        intpuErrors_t[idx] = target_t[idx] - outputVariables_t[idx];
    }
  }

  virtual Vector<real_t> sample(int pt) {
    Vector<real_t> rv(this->plotSize);
    View<real_t> vars = outputVariables[pt];
    for(size_t idx = 0; idx < vars.size(); ++idx) {
        rv[idx] = Random::bernoulli(vars[idx]) ? 1.0 : 0.0;
    }
    return rv;
  }
};

struct BernoulliMixtureSamplingLayer : public BernoulliMixtureOutputLayer {
  Layer *inputLayer;
  int primeLen;

  BernoulliMixtureSamplingLayer(ostream &o,
                                Layer *input,
                                const string &name)
      : BernoulliMixtureOutputLayer(o, name),
        inputLayer(input),
        primeLen(-1) {

  }

  void feed_forward(const vector<int> &coords) {
    BernoulliMixtureOutputLayer::feed_forward(coords);
    sample(coords[0]);
  }

  virtual Vector<real_t> sample(int pt) {
    Vector<real_t> rv = BernoulliMixtureOutputLayer::sample(pt);
    if (pt < primeLen) {
      return rv;
    }
    if (inputLayer->outputActivations.in_range({ pt + 1 })) {
      inputLayer->outputActivations[pt + 1] = rv;
    }
    return rv;
  }

  void set_prime_length(int l) {
    primeLen = l;
  }
};

#endif
