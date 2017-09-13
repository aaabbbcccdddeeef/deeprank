import os 
import sys

import numpy as np
import subprocess as sp


'''
	Assemble the data set from different sources of  decoys/natives/features/targets

	ARGUMENTS

	classID 

			contains a classification of the conformations we want for the training set
			<class> <complex_name>
			where classe is 0 (decoy) or 1 (native) and complex_name the name of the complex
			if present in the class only the complexes specified in this file will be
			generated 

	decoys 

			path to the decoy files generated by HADDOCK
			the script will look for all the pdb files contained 
			in any subdirectory of this folder.

	natives

			path to the native confomrmation
			the script will consider all the pdb files contained here

	features

			dictionnary containing the name and path to the features
			{'PSSM' : path/to/PSSM/files}

	targets

			dictionnary containing the desires targets example
			{'haddock_score' : path/to/hadosck/score}

'''

class DataAssembler(object):

	def __init__(self,classID=None,decoys=None,natives=None,
		         features=None,targets=None,outdir=None):

		self.classID = classID
		self.decoys  = decoys
		self.natives = natives 
		self.features = features
		self.targets = targets
		self.outdir = outdir

	def create_data_folders(self):

		'''
		Create all the data files generate by all the pdb contained
		in the natives + decoys directories
		'''

		# check if we can create a dir here
		self._check_outdir()

		# get all the natives/decoys
		self.natives_names = sp.check_output('ls %s/*.pdb' %self.natives,shell=True).decode('utf8').split()
		self.decoys_names = sp.check_output('find %s -name "*.pdb" ' %self.decoys,shell=True).decode('utf8').split()

		# filter the cplx if required 
		if self.classID is not None:
			self._filter_cplx()

		# create the data files
		self._create_data()

	def add_feature(self):

		'''
		add a feature file to an existing folder arboresence
		only need an output dir and a feature dictionary
		'''

		if not os.path.isdir(self.outdir):
			print(': %s not found' %self.outdir)
			sys.exit()

		# get the folder names
		fnames = sp.check_output('ls -d %s/*/' %self.outdir,shell=True).decode('utf8').split()

		for cplx_name in fnames:

			# names of the molecule
			mol_name = cplx_name.split('/')[-2]
			bare_mol_name = mol_name.split('_')[0]
			cplx_dir_name = self.outdir + '/' + mol_name

			self._add_feat(cplx_dir_name,bare_mol_name)


	def add_target(self):

		'''
		add a target files to an existing folder arboresence
		only need an output dir and a target dictionary
		'''

		if not os.path.isdir(self.outdir):
			print(': %s not found' %self.outdir)
			sys.exit()

		# get the folder names
		fnames = sp.check_output('ls -d %s/*/' %self.outdir,shell=True).decode('utf8').split()

		for cplx_name in fnames:

			# names of the molecule
			mol_name = cplx_name.split('/')[-2]
			target_dir_name = self.outdir + '/' + mol_name + '/targets/'
			self._add_targ(target_dir_name,mol_name)


#====================================================================================

	def _filter_cplx(self):

		# read the class ID
		f = open(self.classID)
		data = f.readlines()
		f.close()

		# create the filters
		tmp_natives_names, tmp_decoys_names = [],[]		
		for line in data:

			line = line.split()
			classid = int(line[0])
			filter_name = line[1]

			if classid == 0:
				tmp_decoys_names += list(filter(lambda x: filter_name in x,self.decoys_names))
			elif classid == 1:
				tmp_natives_names += list(filter(lambda x: filter_name in x,self.natives_names))

		self.natives_names = tmp_natives_names
		self.decoys_names = tmp_decoys_names


	def _create_data(self):

		# loop over the decoys/natives
		for cplx_class,cplx_types in zip([1,0],[self.natives_names,self.decoys_names]):

			# loop over all the complexes
			for cplx in cplx_types:

				print(': Process complex %s' %(cplx))

				# names of the molecule
				mol_name = cplx.split('/')[-1][:-4]
				bare_mol_name = mol_name.split('_')[0]

				# create the subfodler for that molecule
				cplx_dir_name = self.outdir + '/' + mol_name
				os.mkdir(cplx_dir_name)

				# copy the pdb file in it
				sp.call('cp %s %s/complex.pdb' %(cplx,cplx_dir_name),shell=True)

				# add the features
				self._add_feat(cplx_dir_name,bare_mol_name)

				# create the target dir and input the binary class target
				target_dir_name = cplx_dir_name + '/targets/'
				os.mkdir(target_dir_name)
				np.savetxt(target_dir_name + 'binary_class.dat',np.array([cplx_class]),fmt='%d')

				# input the desired targets
				if cplx_class == 0:
					self._add_targ(target_dir_name,mol_name)
					


	def _add_feat(self,cplx_dir_name,bare_mol_name):

		# get all the features
		for feat_name,feat_dir in self.features.items():

			# create the directory
			out_feat_dir = cplx_dir_name + '/' + feat_name
			os.mkdir(out_feat_dir)

			# copy all the files containing the bare mol name in that directory
			sp.call('cp %s/*%s* %s/' %(feat_dir,bare_mol_name,out_feat_dir),shell=True)


	def _add_targ(self,target_dir_name,mol_name):

		for targ_name,targ_dir in self.targets.items():

			# find the correct value and print it
			try:
				tar_val = sp.check_output('grep -w %s %s/*.*' %(mol_name,targ_dir),shell=True).decode('utf8').split()[-1]
				np.savetxt(target_dir_name + targ_name + '.dat',np.array([float(tar_val)]))
			except:
				print('%s target file not found for %s' %(targ_name,mol_name))

	def _check_outdir(self):

		if os.path.isdir(self.outdir):
			print('Output directory %s already exists' %(self.outdir))
			sys.exit()
		else:
			print('New output directory created at %s' %(self.outdir))
			os.mkdir(self.outdir)




if __name__ == "__main__":

	
	BM4 = '/home/nico/Documents/projects/deeprank/data/HADDOCK/BM4_dimers/'

	decoys = BM4 + 'decoys_pdbFLs/'
	natives = BM4 + '/BM4_dimers_bound/pdbFLs_ori'
	features = {'PSSM' : BM4 + '/PSSM'}
	targets = {'haddock_score' : BM4 + '/model_qualities/haddockScore/water'}
	classID = BM4 + '/training_set_IDS/classIDs.lst'
	outdir = '../training_set/'

	da = DataAssembler(classID=classID,decoys=decoys,natives=natives,
		              features=features,targets=targets,outdir=outdir)


	da.create_data_folders()
	

	'''
	targets = {'fnat' : BM4 + '/model_qualities/Fnat/water'}
	outdir = './training_set/'
	da = DataAssembler(targets=targets,outdir=outdir)
	da.add_target()
	'''

	'''
	features = {'PSSM_2' : BM4 + '/PSSM'}
	outdir = './training_set/'
	da = DataAssembler(features=features,outdir=outdir)
	da.add_feature()
	'''