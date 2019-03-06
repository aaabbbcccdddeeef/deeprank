import os
import glob
import numpy as np

from deeprank.learn import *
from deeprank.learn.model3d import cnn as cnn3d

database = './hdf5/*1ak4.hdf5'
out = './out'

# clean the output dir
out = './out_3d'
if os.path.isdir(out):
  for f in glob.glob(out+'/*'):
    os.remove(f)
  os.removedirs(out)


# declare the dataset instance

data_set = DataSet(database,
			valid_database = None,
            test_database = None,
            mapfly=True,
            use_rotation=5,
            grid_info = {'number_of_points':[10,10,10], 'resolution' : [3,3,3]},

            select_feature={'AtomicDensities' : {'CA':3.5, 'C':3.5, 'N':3.5, 'O':3.5},
                			'Features'        : ['coulomb','vdwaals','charge','PSSM_*'] },

            select_target='DOCKQ',
            tqdm=True,
            normalize_features = False,
            normalize_targets=False,
            clip_features=False,
            pair_chain_feature=np.add,
            dict_filter={'DOCKQ':'<1.'})

# create the network
model = NeuralNet(data_set,cnn3d,model_type='3d',task='reg',
                  cuda=False,plot=True,outdir=out)

# start the training
model.train(nepoch = 5, divide_trainset = None, train_batch_size = 5, num_workers=0, save_model='all')
