import os
import shutil
import yaml
import numpy as np

AISPRINT_ANNOTATIONS = ['component_name', 'exec_time', 'expected_throughput', 
                        'partitionable_model', 'device_constraints', 'early_exits_model', 'annotation']

def parse_dag(dag_file):
    with open(dag_file, 'r') as f:
        dag = yaml.safe_load(f) 
    
    dag = dag['System']
    
    dag_dict = {}

    # These will help to find leaf nodes
    source_components = [] 
    target_components = [] 

    for idx, dependency in enumerate(dag['dependencies']):

        # Check dependencies are well formatted
        # e.g., we need [['CX', 'CY', p]]
        if len(dependency) != 3:
            raise Exception("Bad dependencies format in the provided DAG file. " + 
                            "Dependencies must be triplets '['CX', 'CY', Prob.]'.")

        # Get source and target components
        source_c = dependency[0]
        target_c = dependency[1]

        # Save source_c in source_components 
        if not source_c in source_components:
            source_components.append(source_c)
        # Save target_c in target_components 
        if not target_c in target_components:
            target_components.append(target_c)

        # Add component in the dag_dict
        if not source_c in dag_dict:
            dag_dict[source_c] = {'next': [target_c]}
        else:
            if not target_c in dag_dict[source_c]['next']:
                dag_dict[source_c]['next'].append(target_c)
        
    # Find leaf components: 
    # reached by other components but not reaching other components
    for target_c in target_components:
        if target_c not in source_components:
            # Add leaf component as having empty 'next' components 
            if idx == len(dag['dependencies']) - 1:
                dag_dict[target_c] = {'next': []}
    
    # Get total number of components
    num_components = len(dag_dict.keys())
    
    # Check dependencies components and DAG components match
    dependencies_components = np.unique(list(dag_dict.keys()))
    dag_components = np.unique(list(dag['components']))
    
    if not np.all(dependencies_components == dag_components):
        raise Exception("Components in 'dependencies' and 'components' in " + 
                        "the DAG YAML file do not match.")

    return dag_dict, num_components
    
def get_component_folder(application_dir, component_name):
    with open(os.path.join(application_dir, 'common_config', 'annotations.yaml'), 'r') as f:
        annotations_dict = yaml.safe_load(f)

    for main_path, annotations in annotations_dict.items():
        if annotations['component_name']['name'] == component_name:
            return main_path.split('main.py')[0] 

def get_annotation_managers(application_dir):
    ''' Return annotation managers dictionary with items
        annotation: AnnotationManager
    '''

    from .annotations import annotation_managers

    with open(os.path.join(application_dir, 'common_config', 'application_dag.yaml'), 'r') as f:
        dag_dict = yaml.safe_load(f)
    application_name = dag_dict['System']['name'] 

    annotation_managers_dict = {}
    for aisprint_annotation in AISPRINT_ANNOTATIONS:
        if aisprint_annotation == 'annotation':
            continue
        manager_module_name = aisprint_annotation + '_manager'
        manager_class_name = "".join([s.capitalize() for s in manager_module_name.split('_')])
        manager_class = getattr(annotation_managers, manager_class_name)
        annotation_managers_dict[aisprint_annotation] = manager_class(
            application_name=application_name, application_dir=application_dir)
    return annotation_managers_dict

def run_annotation_managers(annotation_managers, deployment_name):
    # Run the annotation manager corresponding to each annotation
    for aisprint_annotation in AISPRINT_ANNOTATIONS:
        if aisprint_annotation == 'annotation':
            continue
        annotation_manager = annotation_managers[aisprint_annotation]
        annotation_manager.generate_configuration_files(deployment_name)