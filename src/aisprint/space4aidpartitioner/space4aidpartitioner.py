import os
import shutil

from tqdm import tqdm

import numpy as np

import onnx
from skl2onnx.helpers.onnx_helper import enumerate_model_node_outputs
from skl2onnx.helpers.onnx_helper import load_onnx_model

from google.protobuf.json_format import MessageToDict


class SPACE4AIDPartitioner():
    ''' Temporary partitioner that, given a partitionable model:
        - Generate the model partitions from the ONNX file. In particular,
            takes the partition with the lowest tensor size.
        - Generate the Python code to execute the partitions
    '''

    def __init__(self, application_dir, partitionable_model, onnx_file):

        self.application_dir = application_dir
        self.partitionable_model = partitionable_model
        self.partitionable_model_dir = os.path.join(
            self.application_dir, 'aisprint', 'designs', partitionable_model, 'base')
        self.onnx_file = os.path.join(self.partitionable_model_dir, 'onnx', onnx_file)
    
    def get_partitions(self):
        # Load the Onnx Model
        print("- Finding partitions of model: {}".format(self.partitionable_model))
        onnx_model = load_onnx_model(self.onnx_file)
        sorted_nodes = self._get_sorted_nodes(onnx_model=onnx_model)
        return self.onnx_model_split_first_smallest(sorted_nodes, onnx_model=onnx_model)

    def _get_node_type(self, onnx_model, node_name):
        for node in onnx_model.graph.node:
            if node_name in node.output:
                return node.op_type
    
    def _node_is_activation(self, node):
        # NOTE: add others?
        if 'relu' in node:
            return True
        if 'tanh' in node:
            return True
        if 'sigmoid' in node:
            return True
        if 'affine' in node:
            return True
        if 'elu' in node:
            return True
        if 'softsign' in node:
            return True
        if 'softplus' in node:
            return True
        return False

    def _get_sorted_nodes(self, onnx_model):
        shape_info = onnx.shape_inference.infer_shapes(onnx_model)
        shape_info_dict = {}
        output_nodes = [node.name for node in onnx_model.graph.output]
        for info in shape_info.graph.value_info:
            info_dict = MessageToDict(info)
            node_name = info_dict['name']
            # Do not consider output nodes
            if node_name in output_nodes:
                continue
            # Do not consider activation nodes TODO: to be double checked 
            node_type = self._get_node_type(
                onnx_model=onnx_model, node_name=node_name)
            if self._node_is_activation(node_type):
                continue
            # Do not consider nodes with no shape 
            # (NOTE: this is only for this implementation)
            if 'shape' in info_dict['type']['tensorType'].keys():
                shape = info_dict['type']['tensorType']['shape']
                if not shape: 
                    continue
            else:
                continue
            
            dims = [int(dim['dimValue']) for dim in shape['dim'] if 'dimValue' in dim]
            num_pixels = np.prod(dims)

            shape_info_dict[node_name] = num_pixels
        
        # Order nodes based on the output tensor
        shape_info_dict_sorted = dict(sorted(shape_info_dict.items(), key=lambda item: item[1]))

        return shape_info_dict_sorted

    def onnx_model_split_first_smallest(self, sorted_nodes, onnx_model=None, number_of_partitions=1):
        ''' Find all the possible partitions of the ONNX model, 
            which are stored as designs in the designs folder of the AI-SPRINT application.
        '''

        designs_folder = os.path.join(
            self.application_dir, 'aisprint', 'designs', self.partitionable_model)
        
        if onnx_model is None:
            # Load the Onnx Model
            onnx_model = load_onnx_model(self.onnx_file)

        found_partitions = []

        #Make a split for every layer in the model
        ln = 0
        # for layer in enumerate_model_node_outputs(onnx_model):
        partitioned_layers = []
        for layer in tqdm(sorted_nodes):
            # Initialize partitions designs folders
            which_partition = 'partition{}'.format(ln+1)
            partition1_dir = os.path.join(designs_folder, which_partition+'_1')
            if not os.path.exists(partition1_dir):
                os.makedirs(partition1_dir)
            partition2_dir = os.path.join(designs_folder, which_partition+'_2')
            if not os.path.exists(partition2_dir):
                os.makedirs(partition2_dir)
            
            onnx_folder = os.path.join(partition2_dir, 'onnx')
            if not os.path.exists(onnx_folder):
                os.makedirs(onnx_folder)

            # Split and save the second half of the current partition 
            # -------------------------------------------------------
            input_names = [layer]

            output_names = []

            for i in range(len(onnx_model.graph.output)):
                output_names.append(onnx_model.graph.output[i].name)

            try:
                onnx.utils.extract_model(
                    self.onnx_file, 
                    os.path.join(onnx_folder, which_partition+'_2.onnx'), 
                    input_names, output_names)
                found_partitions.append(which_partition+'_2')
            except Exception as e:
                # print(e)
                found_partitions = []
                shutil.rmtree(partition1_dir)
                shutil.rmtree(partition2_dir)
                continue
            # -------------------------------------------------------
            
            # Split and save the first half of the current partition 
            # ------------------------------------------------------
            input_names = []
            
            for i in range(len(onnx_model.graph.input)):
                input_names.append(onnx_model.graph.input[i].name)

            output_names = [layer]

            onnx_folder = os.path.join(partition1_dir, 'onnx')
            if not os.path.exists(onnx_folder):
                os.makedirs(onnx_folder)

            onnx.utils.extract_model(self.onnx_file, 
                                     os.path.join(onnx_folder, which_partition+'_1.onnx'), 
                                     input_names, output_names)

            found_partitions.append(which_partition+'_1')

            # Found first smallest partition, then break
            ln = ln + 1

            partitioned_layers.append(layer)

            if ln == number_of_partitions:
                break
                
        print("Model partitioned at layers: {}\n".format(partitioned_layers))
        return found_partitions
        # ------------------------------------------------------
        
        # ln = ln + 1