## Subsampled MH for Bayesian Logistic Regression

import numpy as np
import scipy.io
import time
import shelve
from venture.shortcuts import make_lite_church_prime_ripl
make_ripl = make_lite_church_prime_ripl

def main(data_source_, epsilon_):
  ##########################################
  #### Parameters

  print "data_source:", data_source_
  print "epsilon:", epsilon_

  ## Data
  data_source = data_source_ # "mnist" # "synthetic"

  ## Load data
  if data_source == "synthetic":

    ##### Synthetic Data
    D = 2
    N = 100
    w = np.random.normal(0, np.sqrt(0.1), D + 1).tolist()
    X = np.random.normal(0, 1, [N, D])
    f = X.dot(w[1:]) + w[0]
    y = np.random.random(N) < 1 / (1 + np.exp(-f))
    X = X.tolist()
    y = y.tolist()

  elif data_source == "mnist":

    ##### MNIST Data
    from load_data import loadData
    data_file = 'data/input/mnist_D50_7_9.mat'
    N, D, X, y, _, _, _ = loadData(data_file)
    print "N:", N, "D:", D


  elif data_source == "four_cluster":

    ##### One cluster in four_cluster_data2
    from load_data import loadData
    data_file = 'data/input/four_cluster_data2_one.mat'
    N, D, X, y, _, _, _ = loadData(data_file)

    print "N:", N, "D:", D


  ## Sampler
  time_max = 5e5
  T = 1000000
  Tthin = 1
  Nsamples = (T + Tthin - 1) / Tthin

  Tsave = 100

  # Proposal
  sig_prop = 0.01

  # Austerity
  Nbatch = 100 # 600
  k0 = 3
  epsilon = epsilon_

  use_austerity = epsilon != 0 # False # True
  tag_austerity = "submh_%.2f" % epsilon if use_austerity else "mh"

  # bayeslr_mnist_mh or bayeslr_mnist_submh
  tag = "_".join(["bayeslr_fast_m100_Time5e5", data_source, tag_austerity])

  stage_file = 'data/output/bayeslr/stage_'+tag
  result_file = 'data/output/bayeslr/result_'+tag

  ##########################################
  #### Initialization
  prog = """
  [clear]
  [assume D %d]
  [assume mu (zeros_array (+ D 1))]
  [assume Sigma (diagonal_matrix (scalar_product (sqrt 0.1) (ones_array (+ D 1))))]
  [assume w (scope_include (quote w) 0 (multivariate_normal mu Sigma))]
  [assume y_x (lambda (x) (bernoulli (linear_logistic w x)))]
  """ % D
  v = make_ripl()
  v.execute_program(prog);

  ## Load observations.
  tic = time.clock()
  for n in xrange(N):
    if (n + 1) % round(N / 10) == 0:
      print "Processing %d/%d observations." % (n + 1, N)
    v.observe('(scope_include (quote y) %d (y_x (array %s)))' \
              % (n, ' '.join(['%f' % x for x in X[n]])), y[n])
  t_obs = time.clock() - tic
  print "It takes", t_obs, "seconds to load observations."

  rst = {'ts': list(),
         'ws': list()}

  ##########################################
  #### Run and Record

  v.infer('(mh w all 1)') # First iteration to run engine.incorporate whose running time is excluded from record.

  t_start = time.clock()
  i_save = -1
  for i in xrange(Nsamples):
    # Run inference.
    if not use_austerity:
      v.infer('(mh w all %d true %s)' % (Tthin, repr(sig_prop)))
    else:
      v.infer('(subsampled_mh w all %d %d %d %s true %s)' % (Tthin, Nbatch, k0, repr(epsilon), repr(sig_prop)))

    # Record.
    rst['ts'].append(time.clock() - t_start)
    rst['ws'].append(v.sample('w'))

    # Save temporary results.
    if (i + 1) % Tsave == 0:
      scipy.io.savemat(stage_file, rst)
      i_save = i

    time_run = time.clock() - t_start
    print i, "/", Nsamples, "time:", time_run
    if time_run > time_max:
      break

  # If savemat is not called at the last iteration, call it now.
  if i_save != i:
    scipy.io.savemat(stage_file, rst)

  ## Plotting.
  #plot(rst['ts'], [w[0] for w in rst['ws']], 'x-')

  ##########################################
  #### Save workspace
  from cPickle import PicklingError
  my_shelf = shelve.open(result_file,'n') # 'n' for new
  for key in dir():
    try:
      my_shelf[key] = locals()[key]
    except (TypeError, PicklingError):
      #
      # __builtins__, my_shelf, and imported modules can not be shelved.
      #
      print('Not shelved: {0}'.format(key))
  my_shelf.close()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--data', dest='data_source_', default='mnist', help='data file')
  parser.add_argument('--eps',dest='epsilon_', default=0.0, type=float, help='Epsilon')
  args = vars(parser.parse_args())
  main(**args)

