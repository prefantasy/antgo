# -*- coding: UTF-8 -*-
# @Time    : 17-6-22
# @File    : trainer.py
# @Author  : jian<jian@mltalker.com>
from __future__ import division
from __future__ import unicode_literals

import tensorflow as tf
import re
from abc import ABCMeta, abstractmethod
from antgo.context import *
import collections


DefaultParam = collections.namedtuple('DefaultParam', ['name', 'value', 'help'])


trainer_default_params = [
  DefaultParam('batch_size', 1, 'The number of samples in each batch.'),
  DefaultParam('max_epochs', 100, ''),
  DefaultParam('num_samples', 0, ''),
  DefaultParam('snapshot_prefix', 'alpha', ''),
  DefaultParam('snapshot_infix', 'train', ''),
  DefaultParam('num_clones', 1, 'Number of model clones to deploy'),
  DefaultParam('devices', [], 'clone is deployed at devices'),
  DefaultParam('clone_on_cpu', False, 'Use CPUs to deploy clones'),
  DefaultParam('worker_replicas', 1, 'Number of worker replicas'),
  DefaultParam('num_ps_tasks', 0, 'The number of parameter servers. If the value is 0, then the parameters are handled locally by the worker.'),
  DefaultParam('log_every_n_steps', 50, 'The frequency with which logs are print'),
  DefaultParam('replica_id', 0, 'Task id of the replica running the training.'),
  DefaultParam('weight_decay', 0.00004, 'The weight decay on the model weights.'),
  DefaultParam('optimizer', 'rmsprop', 'The name of the optimizer, one of "adadelta", "adagrad", "adam", "ftrl", "momentum", "sgd" or "rmsprop".'),
  DefaultParam('adadelta_rho', 0.95, 'The decay rate for adadelta.'),
  DefaultParam('adagrad_initial_accumulator_value', 0.1, 'Starting value for the AdaGrad accumulators'),
  DefaultParam('adam_beta1', 0.9, 'The exponential decay rate for the 1st moment estimates.'),
  DefaultParam('adam_beta2', 0.999, 'The exponential decay rate for the 2nd moment estimates'),
  DefaultParam('opt_epsilon', 1e-6, 'Epsilon term for the optimizer.'),
  DefaultParam('ftrl_learning_rate_power', -0.5, 'The learning rate power.'),
  DefaultParam('ftrl_initial_accumulator_value', 0.1, 'Starting value for the FTRL accumulators.'),
  DefaultParam('ftrl_l1', 0.0, 'The FTRL l1 regularization strength'),
  DefaultParam('ftrl_l2', 0.0, 'The FTRL l2 regularization strength.'),
  DefaultParam('momentum', 0.9, 'The momentum for the MomentumOptimizer and RMSPropOptimizer.'),
  DefaultParam('rmsprop_momentum', 0.95, 'Momentum'),
  DefaultParam('rmsprop_decay', 0.9, 'Decay term for RMSProp.'),
  DefaultParam('learning_rate_decay_type', 'polynomial', 'Specifies how the learning rate is decayed. One of "fixed", "exponential", or "polynomial"'),
  DefaultParam('learning_rate', 0.01, 'Initial learning rate'),
  DefaultParam('end_learning_rate', 0.0001, 'The minimal end learning rate used by a polynomial decay learning rate'),
  DefaultParam('learning_rate_decay_factor', 0.94, 'Learning rate decay factor'),
  DefaultParam('num_epochs_per_decay', 20, 'Number of epochs after which learning rate decays.'),
  DefaultParam('sync_replicas', False, 'Whether or not to synchronize the replicas during training.'),
  DefaultParam('replicas_to_aggregate', 1, 'The Number of gradients to collect before updating params.'),
  DefaultParam('moving_average_decay', None, 'The decay to use for the moving average.'),
  DefaultParam('checkpoint_path', None, ''),
  DefaultParam('checkpoint_exclude_scopes', None, ''),
  DefaultParam('checkpoint_transfer_scopes', None, ''),
  DefaultParam('regularization_loss', True, ''),
  DefaultParam('trainable_filter', None, ''),
  DefaultParam('dataset_queue_threads', 1, '')
]


class Trainer(object):
    def __init__(self, trainer_context=None, is_training=True):
        # 1.step config trainer context
        for param in trainer_default_params:
          k = param.name
          v = param.value
          if trainer_context is not None:
              setattr(self, k, getattr(trainer_context, k, v))
          else:
              setattr(self, k, v)

        self._trainer_context = trainer_context

        # 3.step other
        self.iter = 0
        self.is_training = is_training

        # context
        self.ctx = get_global_context()
        self.ctx.registry_clear_callback(self.wait_until_clear)
        
    def deploy(self, model):
        pass

    def run(self, data_generator, binds):
        if self.ctx is not None:
            for k, v, c, f in self.ctx.registried_trainer_callbacks:
                cur_value = getattr(self, k, None)
                if cur_value is not None:
                    if c == 'equal':
                        if cur_value == v:
                            f()
                    elif c == 'less':
                        if cur_value < v:
                            f()
                    elif c == 'greater':
                        if cur_value > v:
                            f()
                    elif c == 'mod':
                        if int(cur_value) % int(v) == 0:
                            f()

    def snapshot(self, dump_dir, epoch):
        pass

    def watch(self, name, fuzzy=True):
        # add watch var list
        pass

    @property
    def iter_at(self):
        return self.iter
    @iter_at.setter
    def iter_at(self, val):
        self.iter = val

    def wait_until_clear(self):
        pass


class ModelDesc(object):
  __metaclass__ = ABCMeta

  def __init__(self, model_name=None):
    if model_name is not None:
      self.model_name = model_name
    else:
      self.model_name = self.__class__.__name__
  
    self._ctx = None

  @property
  def name(self):
    return self.model_name

  @property
  def ctx(self):
    return self._ctx
  @ctx.setter
  def ctx(self, val):
    self._ctx = val
    for k in dir(self._ctx):
      if not k.startswith('__'):
        setattr(self, k, getattr(self._ctx, k, None))
  
  @property
  def need_feed(self):
    return self._need_feed
  @need_feed.setter
  def need_feed(self, val):
    self._need_feed = val
    
  def model_input(self, is_training, data_source):
    return None
  
  @abstractmethod
  def model_fn(self, is_training=True, *args, **kwargs):
    '''
    :return: 
    '''