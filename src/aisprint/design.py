import os
import argparse 
import yaml

from .utils import parse_dag
from .designs_creation import create_aisprint_designs
from .annotations_parsing import run_aisprint_parser
from .deployments_creation import create_aisprint_deployments

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
    dag_file = os.path.join(application_dir, 'application_dag.yaml')
    
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

    # 3) Create AI-SPRINT components' designs 
    # ---------------------------------------
    create_aisprint_designs(application_dir=application_dir)
    # ---------------------------------------

    # 4) Create AI-SPRINT deployments 
    create_aisprint_deployments(application_dir=application_dir) 
    # -------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--application_dir", help="Path to the AI-SPRINT application.", required=True)
    args = vars(parser.parse_args())

    application_dir = args['application_dir']

    run_design(application_dir=application_dir)
    