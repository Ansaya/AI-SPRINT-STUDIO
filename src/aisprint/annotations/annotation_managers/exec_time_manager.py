import os
import yaml 

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
                partition_of = dag_component.rsplit('_', 1)[0]
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
                    if not 'local_constraints' in qos_constraints['system']:
                        qos_constraints['system']['local_constraints'] = {}
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
                            prev_partition_of = prev_component.rsplit('_', 1)[0]
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
                    if not 'global_constraints' in qos_constraints['system']:
                        qos_constraints['system']['global_constraints'] = {}
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
                partition_of = dag_component.rsplit('_', 1)[0]  # This gives 'CX' in the example
                
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
                    if not 'global_constraints' in qos_constraints['system']:
                        qos_constraints['system']['global_constraints'] = {}
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
                            prev_partition_of = prev_component.rsplit('_', 1)[0]
                            prev_partitions = sorted(partitions_dict[prev_partition_of]['partitions'])
                            for prev_partition in prev_partitions:
                                if prev_partition != dag_component:
                                    new_prev_components.append(prev_partition)
                    # Finally, add the component itself
                    new_prev_components.append(dag_component)
                    
                    # Save global constraint
                    global_constraint_idx += 1
                    if not 'global_constraints' in qos_constraints['system']:
                        qos_constraints['system']['global_constraints'] = {}
                    qos_constraints['system']['global_constraints'][
                        'global_constraint_'+str(global_constraint_idx)] = {
                            'components_path': new_prev_components, 'threshold': global_time_thr}
        
        return qos_constraints

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

        # Save QoS constraints file for AMS
        qos_filename = os.path.join(self.deployments_dir, deployment_name, 'ams', 'qos_constraints.yaml')
        with open(qos_filename, 'w') as f:
            yaml.dump(qos_constraints, f) 