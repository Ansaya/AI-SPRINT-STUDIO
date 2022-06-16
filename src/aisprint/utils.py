import os
import shutil
import yaml
import numpy as np

from .annotations.annotations_parser import QoSAnnotationsParser

def parse_dag(dag_file):
    with open(dag_file, 'r') as f:
        dag = yaml.load(f) 
    
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
    
def parse_annotations(src_dir):
    # Get the directories of the components
    components_dirs = next(os.walk(src_dir))[1]

    # For each component dir, find annotations in 'main.py' 
    # First check that a 'main.py' exists for each partition
    missing_mains = []
    for component_dir in components_dirs:
        filenames = next(os.walk(os.path.join(src_dir, component_dir)))[2]

        if 'main.py' not in filenames:
            missing_mains.append(component_dir)
    
    if missing_mains != []:
        error_msg = "'main.py' script missing for the following components: "
        for mm in missing_mains:
            error_msg += "{}; ".format(mm)
        raise RuntimeError(error_msg)

    # Parse
    annotations_dict = {}
    for component_dir in components_dirs:
        main_script = os.path.join(src_dir, component_dir, 'main.py')

        qos_annot_parser = QoSAnnotationsParser(main_script) 
        annotations_dict[main_script] = qos_annot_parser.parse()
    
    return annotations_dict

def copy_project_structure(source_dir, destination_dir, application_name):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    shutil.copytree(os.path.join(source_dir, 'src'), 
                    os.path.join(destination_dir, 'src'))
    shutil.copytree(os.path.join(source_dir, 'space4ai-d'), 
                    os.path.join(destination_dir, 'space4ai-d'))
    shutil.copytree(os.path.join(source_dir, 'oscar'), 
                    os.path.join(destination_dir, 'oscar'))
    shutil.copytree(os.path.join(source_dir, 'onnx'), 
                    os.path.join(destination_dir, 'onnx'))
    shutil.copytree(os.path.join(source_dir, 'pycomps'), 
                    os.path.join(destination_dir, 'pycomps'))
    shutil.copytree(os.path.join(source_dir, 'im'), 
                    os.path.join(destination_dir, 'im'))
    shutil.copytree(os.path.join(source_dir, 'ams'), 
                    os.path.join(destination_dir, 'ams'))
    shutil.copyfile(os.path.join(source_dir, 'application_dag.yaml'), 
                    os.path.join(destination_dir, 'application_dag.yaml'))