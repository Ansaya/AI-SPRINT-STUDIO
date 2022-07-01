from email.mime import application
import os
import argparse 

from aisprint.application_preprocessing import ApplicationPreprocessor
from aisprint.deployments_generators import BaseDeploymentGenerator

from .utils import parse_dag, get_annotation_manager
from .annotations_parsing import run_aisprint_parser

def run_design(application_dir):

    """ Execute the AI-SPRINT pipeline to create the possible application designs:
        
        1. Read DAG file
        2. Parse AI-SPRINT annotations
        3. Create components' designs 
        4. Create AI-SPRINT possible deployments 
    """

    print("\n")
    print("# --------- #")
    print("# AI-SPRINT #")
    print("# --------- #")
    print("# --------- #")
    print("#   Design  #")
    print("# --------- #")
    print("\n")

    # 1) Read DAG file
    # ----------------
    # DAG filename: 'application_dag.yaml' 
    dag_file = os.path.join(application_dir, 'common_config', 'application_dag.yaml')
    
    print("Parsing application DAG in '{}'..".format(dag_file))
    dag_dict, num_components = parse_dag(dag_file)

    print("* Found {} components in the DAG with the following dependencies:\n".format(num_components))
    for component, next_component in dag_dict.items():
        print("* {} -> {}".format(component, next_component))
    print("")
    
    # Get the directories of the components
    components_dirs = next(os.walk(os.path.join(application_dir, 'src')))[1]

    # Check number of directories is equal to the number of components in the DAG
    if len(components_dirs) != num_components:
        raise RuntimeError(
            "Number of components in the DAG does not match the number of directories in 'src'")

    # ----------------

    # 2) Parse and validate AI-SPRINT annotations
    # -------------------------------------------
    run_aisprint_parser(application_dir=application_dir)
    # -------------------------------------------

    # 3) Create AI-SPRINT base design with the Application Pre-Processor 
    # ------------------------------------------------------------------
    application_preprocessor = ApplicationPreprocessor(application_dir=application_dir)
    application_preprocessor.create_base_design()
    # ---------------------------------------

    # 4) Run SPACE4AI-D-partitioner
    # -----------------------------
    # -----------------------------

    # 5) Create AI-SPRINT base deployment with BaseDeploymentGenerator
    base_deployment_generator = BaseDeploymentGenerator(application_dir)
    base_deployment_generator.create_deployment(deployment_name='base', 
        dag_filename=os.path.join(application_dir, 'common_config', 'application_dag.yaml'))
    # -------------------------------

    # 6) Run annotation managers for optimal deployment
    # (e.g., exec_time to generate the constraints)
    # -------------------------------------------------

    # Run exec_time annotation manager for optimal deployment 
    annotation_manager = get_annotation_manager(
        application_dir=application_dir, which_annotation='exec_time')
    optimal_deployment_symlink = os.path.join(
        application_dir, 'aisprint', 'deployments', 'optimal_deployment')
    optimal_deployment_name = os.path.basename(
        os.path.normpath(os.readlink(optimal_deployment_symlink)))
    print("Generating QoS constraints for the optimal deployment..", end=' ')
    input_args = {'deployment_name': optimal_deployment_name}
    annotation_manager.process_annotations(input_args)

    print("DONE.\n")
    # -------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--application_dir", help="Path to the AI-SPRINT application.", required=True)
    args = vars(parser.parse_args())

    application_dir = args['application_dir']

    run_design(application_dir=application_dir)
    