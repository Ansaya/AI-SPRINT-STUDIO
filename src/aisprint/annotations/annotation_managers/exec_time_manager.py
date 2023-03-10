import os
import yaml 

import numpy as np
from itertools import chain, combinations

from .annotation_manager import AnnotationManager
from aisprint.utils import parse_dag

class ExecTimeManager(AnnotationManager):

    ''' 'exec_time' annotation manager.

        It provides the methods to read the time constraints from the defined annotations.

        Parameters:
            annotations_file (str): complete path to the parsed annotations' file.
        
        NOTE: the annotations are assumed to be already parsed by the QoSAnnotationsParser, which
        also check errors in the annotations' format.
    '''

    def get_qos_constraints(self, dag_file):
        ''' Given the 'base' annotations, the DAG of a specific deployment, and the file providing
            the component_name of the alternative partitions generated from a component,
            generate a new annotation file.
        '''

        with open(dag_file, 'r') as f:
            dag_dict = yaml.safe_load(f)

        # Get components names from DAG dictionary.
        # This includes potentially the new component names due to the partitions.
        dag_components = dag_dict['System']['components'] 
        # Get original annotations components from the original annotations YAML file
        annotations_components = [
            annotations['component_name']['name'] for _, annotations in self.annotations.items()]
        # Parse the dag to obtain the dictionary in the format {'CX': {'next': [CY]}}
        parsed_dag, _ = parse_dag(dag_file)

        # Build a partitions dictionary with the format:
        # {'CX': {'partitions': ['CX_1', 'CX_2'], 'last': 'CX_2'}} 
        # It is used later to easily obtain the partitions of a component and 
        # to identify the last one in the workflow. 
        partitions_dict = {}
        for dag_component in dag_components:
            if dag_component in annotations_components:
                partitions_dict[dag_component] = []
            else:
                partition_of = dag_component.rsplit('_partition', 1)[0]
                if partition_of in partitions_dict:
                    partitions_dict[partition_of]['partitions'].append(dag_component) 
                else:
                    partitions_dict[partition_of] = {'partitions': [dag_component]}

                # Check the dag_component is the last one
                if partition_of not in parsed_dag[dag_component]['next']:
                    partitions_dict[partition_of]['last'] = dag_component
        
        # Build a dictionary with a structure similar to the one of the original annotations
        # but only with the 'exec_time'. To be used later to obtain the local and global constraints
        dag_corrected_annotations = {}

        qos_constraints = {'system': {}}
        qos_constraints['system']['name'] = self.application_name
        qos_constraints['system']['local_constraints'] = {}
        qos_constraints['system']['global_constraints'] = {}

        local_constraint_idx = 0
        global_constraint_idx = 0

        for dag_component in dag_components:
            if dag_component in annotations_components:
                # In this case the component in the DAG is also in the original
                # annotations. This means that it has no partitions in the current deployment.

                # Get the original 'exec_time' annotations and arguments
                original_exec_time = None 
                for _, annotations in self.annotations.items():
                    if (dag_component == annotations['component_name']['name'] and 
                            'exec_time' in annotations):
                        original_exec_time = annotations['exec_time']
                        break

                if original_exec_time is None:
                    # Component 'dag_component' is not 'exec_time'-annotated
                    continue

                if 'local_time_thr' in original_exec_time.keys():
                    # No need to modify, simply get a local constraint from annotation 
                    local_time_thr = original_exec_time['local_time_thr']

                    # Save local constraint
                    local_constraint_idx += 1
                    qos_constraints['system']['local_constraints'][
                        'local_constraint_'+str(local_constraint_idx)] = {
                            'component_name': dag_component, 'threshold': local_time_thr}

                # We need to be robust to the case in which a component is not partitioned
                # but it is originally involved into a global constraints and at least 
                # one of the 'previous_components' has been partitioned instead. 
                # In that case, we need to update the prev_components list.
                if 'global_time_thr' in original_exec_time.keys():
                    # Get original global_time_thr and prev_components 
                    global_time_thr = original_exec_time['global_time_thr']
                    prev_components = original_exec_time['prev_components']
                    # Get the new list of components, in which we substitute a component
                    # with its partitions (if it is partitioned in the DAG.).
                    new_prev_components = []
                    for prev_component in prev_components:
                        if prev_component in dag_components:
                            # prev_component not partitioned -> append as it is
                            new_prev_components.append(prev_component)
                        else:
                            # prev_component partitioned -> append the *ordered* partitions 
                            prev_partition_of = prev_component.rsplit('_partition', 1)[0]
                            prev_partitions = sorted(partitions_dict[prev_partition_of]['partitions'])
                            for prev_partition in prev_partitions:
                                if prev_partition != dag_component:
                                    new_prev_components.append(prev_partition)
                    # Finally, add the component itself
                    new_prev_components.append(dag_component)

                    # Update final 'exec_time' annotations dictionary
                    # by copying the original global_time_thr and by adding the new prev_components 
                    # dag_corrected_annotations.setdefault(dag_component, {})
                    # dag_corrected_annotations[dag_component].setdefault(
                    #     'exec_time', {'global_time_thr': global_time_thr, 'prev_components': new_prev_components})

                    # Save global constraint
                    global_constraint_idx += 1
                    qos_constraints['system']['global_constraints'][
                        'global_constraint_'+str(global_constraint_idx)] =  {
                            'components_path': new_prev_components, 'threshold': global_time_thr}
            else:
                # In this case the component in the DAG is not in the original annotations.
                # This means that the name of that component has been changed, and this can happen
                # only after the partitioning/early-exits tool create new partitions.
                # We need to check if the original component was involved into a local or global constraint
                # and, eventually change annotations accordingly.

                # Get the original component_name (i.e., partition_of)
                # We assume that the partitions have the same name + an enumeration, i.e., 
                # 'CX_1', 'CX_2', ... 
                partition_of = dag_component.rsplit('_partition', 1)[0]  # This gives 'CX' in the example
                
                # Get the original 'exec_time' annotations and arguments
                original_exec_time = None 
                for _, annotations in self.annotations.items():
                    if (partition_of == annotations['component_name']['name'] and 
                            'exec_time' in annotations):
                        original_exec_time = annotations['exec_time']
                        break
                
                if original_exec_time is None:
                    # Original component was not 'exec_time'-decorated -> do nothing
                    continue
                
                if dag_component != partitions_dict[partition_of]['last']:
                    # If it is not the last component, we do not need to provide an annotation.
                    # Since both in the case of local or global constraints only the last partition
                    # is annotated. 
                    continue

                if 'local_time_thr' in original_exec_time.keys():
                    # Original component is involved in a local constraint
                    # then we must add a global constraints on the partitions where
                    # - global_time_thr is the original local_time_thr
                    # - prev_components is the *oredered* list of partitions

                    # Get original global_time_thr and prev_components 
                    global_time_thr = original_exec_time['local_time_thr']
                    # NOTE: sorting is a good option if we reasonably imagine a number of
                    # consecutive partitions < 10
                    new_prev_components = sorted(partitions_dict[partition_of]['partitions'])
                    
                    # Save global constraint
                    global_constraint_idx += 1
                    qos_constraints['system']['global_constraints'][
                        'global_constraint_'+str(global_constraint_idx)] = {
                            'components_path': new_prev_components, 'threshold': global_time_thr}
                    
                if 'global_time_thr' in original_exec_time.keys():
                    # Original component is involved in a global constraint
                    # then we must add a global constraints on the partitions + original prev_components where
                    # - global_time_thr is the original global_time_thr
                    # - prev_components is the *oredered* list of partitions + 
                    #       the original prev_components (eventually partitioned)
                        
                    global_time_thr = original_exec_time['global_time_thr']
                    prev_components = original_exec_time['prev_components']
                    new_prev_components = []
                    for prev_component in prev_components:
                        if prev_component in dag_components:
                            new_prev_components.append(prev_component)
                        else:
                            prev_partition_of = prev_component.rsplit('_partition', 1)[0]
                            prev_partitions = sorted(partitions_dict[prev_partition_of]['partitions'])
                            for prev_partition in prev_partitions:
                                if prev_partition != dag_component:
                                    new_prev_components.append(prev_partition)
                    # Finally, add the component itself and its partitions
                    # NOTE: sorting is a good option if we reasonably imagine a number of
                    # consecutive partitions < 10
                    for part in sorted(partitions_dict[partition_of]['partitions']):
                        new_prev_components.append(part)
                    
                    # Save global constraint
                    global_constraint_idx += 1
                    qos_constraints['system']['global_constraints'][
                        'global_constraint_'+str(global_constraint_idx)] = {
                            'components_path': new_prev_components, 'threshold': global_time_thr}
        
        self.dag_dict = dag_dict
        
        return qos_constraints
    
    def generate_multicluster_qos(self, qos_constraints):
        local_constraints = qos_constraints['system']['local_constraints']
        global_constraints = qos_constraints['system']['global_constraints']
        
        dag_components = self.dag_dict['System']['components']
        
        l_idx = 1
        g_idx = 1

        # Generate each possible layer-component association 
        # Read candidate_deployments.yaml file
        candidate_file = os.path.join(self.application_dir, 'common_config', 'candidate_deployments.yaml')
        with open(candidate_file, 'r') as f:
            candidates = yaml.safe_load(f)
        
        # Get all components name
        components_names = self.dag_dict['System']['components'] 
        # Substitute 'partition1', 'partition2', ecc. with 'partitionX'
        components_layers = {}
        partition_numbers = []
        for cname in components_names:
            splitted_name = cname.rsplit('_partition', 1)
            if len(splitted_name) == 1: # No partition
                new_name = cname
            else:
                partition_number, segment_number = splitted_name[1].split('_')
                partition_numbers.append(int(partition_number))
                new_name = splitted_name[0] + '_partitionX_' + segment_number 
        
            # Get candidate(s) for the current 'cname'
            candidates_components = candidates['Components']
            for candidate_component in candidates_components:
                if candidates_components[candidate_component]['name'] == new_name:
                    candidate_layers = candidates_components[candidate_component]['candidateExecutionLayers']
                    for candidate_layer in candidate_layers:
                        if candidate_layer not in components_layers:
                            components_layers[candidate_layer] = [] 
                        if not cname in components_layers[candidate_layer]:
                            components_layers[candidate_layer].append(cname)
                    break
        
        return_dict = {}
        found_throughput_component = None
        for candidate_layer in components_layers.keys():
            base_qos_name = 'L{}.yaml'.format(candidate_layer)

            # Select mandatory assignments
            component_in_others = False 
            mandatory_components = []
            variable_components = []
            for component in components_layers[candidate_layer]:
                for other_candidate_layer in components_layers.keys():
                    if other_candidate_layer != candidate_layer:
                        if component in components_layers[other_candidate_layer]:
                            component_in_others = True 
                            break
                    if component_in_others:
                        break
                if not component_in_others:
                    mandatory_components.append(component)
                else:
                    variable_components.append(component)
            
            # Get all possible combinations of variable components
            subgs = chain.from_iterable(combinations(variable_components, r) for r in range(len(variable_components)+1))
            subgs = list(subgs)

            # Each subgroup generates a new qos_constraints.yaml file
            l_idx = 1
            g_idx = 1
            for subg in subgs:
                if len(subg) == 0:
                    curr_assignment = mandatory_components
                else:
                    curr_assignment = mandatory_components + list(subg)
                
                # Generate qos_constraints
                qos_name = '' + base_qos_name
                qos_layer = {'system': {}}
                qos_layer['system']['name'] = qos_constraints['system']['name']
                qos_layer['system']['local_constraints'] = {} 
                qos_layer['system']['global_constraints'] = {} 
                for component in curr_assignment:
                    for _, local_constraint in local_constraints.items():
                        if local_constraint['component_name'] == component:
                            qos_layer['system']['local_constraints'][
                                'local_constraint_{}'.format(l_idx)] = {'component_name': component,
                                                                        'threshold': local_constraint['threshold']}
                            l_idx += 1
                    for _, global_constraint in global_constraints.items():
                        if global_constraint['components_path'][-1] == component:
                            qos_layer['system']['global_constraints'][
                                'global_constraint_{}'.format(g_idx)] = {'path_components': global_constraint['components_path'], 
                                                                        'threshold': global_constraint['threshold']}
                            g_idx += 1

                    qos_name = component + '_' + qos_name 
                    
                qos_layer['system']['throughput_component'] = {} 
                
                if found_throughput_component is None:
                    for _, annotations in self.annotations.items():
                        if 'expected_throughput' in annotations:
                            throughput_component = annotations['component_name']['name']
                            if throughput_component in curr_assignment:
                                qos_layer['system']['throughput_component'] = annotations['component_name']['name']
                                found_throughput_component = annotations['component_name']['name']
                            for curr_component in curr_assignment:
                                if throughput_component == curr_component.rsplit('_partition', 1)[0]:
                                    qos_layer['system']['throughput_component'] = curr_component
                                    found_throughput_component = curr_component 
                else:
                    qos_layer['system']['throughput_component'] = found_throughput_component
                
                return_dict[qos_name] = qos_layer
        return return_dict

    def process_annotations(self, args):
        ''' Process annotations dictionary to compute the local/global time constraints.

            Input:
                - args: Python dict with the following items
                    - deployment_name: name of the deployment
        '''
        deployment_name = args['deployment_name'] 

        #  Need to use DAG in the case of partitions
        dag_file = os.path.join(self.deployments_dir, deployment_name, 'application_dag.yaml')

        # Use the DAG as additional information
        qos_constraints = self.get_qos_constraints(dag_file=dag_file)

        qos_layer_dict = self.generate_multicluster_qos(qos_constraints)

        for qos_name, qos_layer in qos_layer_dict.items():
            # Save QoS constraints file for AMS
            qos_filename = os.path.join(
                self.deployments_dir, deployment_name, 'ams', 'qos_constraints_{}'.format(qos_name))
            with open(qos_filename, 'w') as f:
                yaml.dump(qos_layer, f, sort_keys=False) 