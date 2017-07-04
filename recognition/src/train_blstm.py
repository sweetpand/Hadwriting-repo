from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import time
import numpy as np
import tensorflow as tf
import model_blstm


FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('data_dir', '../data/',
                           "data directory")
tf.app.flags.DEFINE_string('checkpoints_dir', '../checkpoints/',
                           "training checkpoints directory")
tf.app.flags.DEFINE_string('log_dir', '../train_log/',
                           "summary directory")
tf.app.flags.DEFINE_integer('batch_size', 128,
                            "mini-batch size")
tf.app.flags.DEFINE_integer('total_epoches', 300,
                            "total training epoches")
tf.app.flags.DEFINE_integer('hidden_size', 128,
                            "size of LSTM hidden memory")
tf.app.flags.DEFINE_integer('num_layers', 1,
                            "number of stacked blstm")
tf.app.flags.DEFINE_integer("input_dims", 3,
                            "input dimensions")
tf.app.flags.DEFINE_integer("num_classes", 69, # 68 letters + 1 blank
                            "num_labels + 1(blank)")
tf.app.flags.DEFINE_integer('log_freq', 10,
                            "how many times showing the mean loss per epoch")
tf.app.flags.DEFINE_float('learning_rate', 0.01,
                          "learning rate of RMSPropOptimizer")
tf.app.flags.DEFINE_float('decay_rate', 0.99,
                          "decay rate of RMSPropOptimizer")
tf.app.flags.DEFINE_float('momentum', 0.9,
                          "momentum of RMSPropOptimizer")


class ModelConfig(object):
    """
    testing config
    """

    def __init__(self):
        self.data_dir = FLAGS.data_dir
        self.checkpoints_dir = FLAGS.checkpoints_dir
        self.log_dir = FLAGS.log_dir
        self.batch_size = FLAGS.batch_size
        self.total_epoches = FLAGS.total_epoches
        self.hidden_size = FLAGS.hidden_size
        self.num_layers = FLAGS.num_layers
        self.input_dims = FLAGS.input_dims
        self.num_classes = FLAGS.num_classes
        self.log_freq = FLAGS.log_freq
        self.learning_rate = FLAGS.learning_rate
        self.decay_rate = FLAGS.decay_rate
        self.momentum = FLAGS.momentum

    def show(self):
        print("data_dir:", self.data_dir)
        print("checkpoints_dir:", self.checkpoints_dir)
        print("log_dir:", self.log_dir)
        print("batch_size:", self.batch_size)
        print("total_epoches:", self.total_epoches)
        print("hidden_size:", self.hidden_size)
        print("num_layers:", self.num_layers)
        print("input_dims:", self.input_dims)
        print("num_classes:", self.num_classes)
        print("log_freq:", self.log_freq)
        print("learning_rate:", self.learning_rate)
        print("decay_rate:", self.decay_rate)
        print("momentum:", self.momentum)


def train_model():
    with tf.get_default_graph().as_default() as graph:
        # config setting
        config = ModelConfig()
        config.show()
        # load data
        # [textline_id, length, 3], 3->(x', y', time)
        input_data = np.load('data.npy')
        label_data = np.load('dense.npy')
        seq_len_list = []
        for _, v in enumerate(input_data):
            seq_len_list.append(v.shape[0])
        seq_len_list = np.array(seq_len_list)
        k = np.argmax(seq_len_list)
        max_length = input_data[k].shape[0]
        # padding each textline to maximum length -> max_length (1939)
        padded_input_data = []
        for _, v in enumerate(input_data):
            residual = max_length - v.shape[0]
            padding_array = np.zeros([residual, 3])
            padded_input_data.append(
                np.concatenate([v, padding_array], axis=0))
        padded_input_data = np.array(padded_input_data)
        # number of batches
        num_batch = int(label_data.shape[0] / config.batch_size)
        # model
        model = model_blstm.HWRModel(config, graph)

        init = tf.global_variables_initializer()
        # Session
        with tf.Session() as sess:
            sess.run(init)
            # loss evaluation
            epoches_loss_sum = 0.0
            counter = 0
            # time cost evaluation
            start_time = time.time()
            end_time = 0.0
            for e in range(config.total_epoches):
                # Shuffle the data
                shuffled_indexes = np.random.permutation(input_data.shape[0])
                input_data = input_data[shuffled_indexes]
                seq_len_list = seq_len_list[shuffled_indexes]
                label_data = label_data[shuffled_indexes]
                for b in range(num_batch):
                    batch_idx = b * config.batch_size
                    # input
                    input_batch = padded_input_data[batch_idx:batch_idx +
                                                    config.batch_size]
                    # sequence length
                    seq_len_batch = seq_len_list[batch_idx:batch_idx +
                                                    config.batch_size]
                    # label
                    dense_batch = label_data[batch_idx:batch_idx +
                                                config.batch_size]
                    # train
                    gloebal_step, losses = model.step(sess, input_batch,
                                        seq_len_batch, dense_batch)
                    epoches_loss_sum += losses
                    counter += 1

                    # logging
                    if b % (num_batch // FLAGS.log_freq) == 0:
                        end_time = time.time()
                        print("%d epoches, %d steps, mean loss: %f, time cost: %f(sec)" %
                                (e,
                                gloebal_step,
                                epoches_loss_sum / counter,
                                end_time - start_time))
                        epoches_loss_sum = 0.0
                        counter = 0
                        start_time = end_time


def main(_):
    train_model()


if __name__ == "__main__":
    if not os.path.exists(FLAGS.checkpoints_dir):
        os.makedirs(FLAGS.checkpoints_dir)
    tf.app.run()