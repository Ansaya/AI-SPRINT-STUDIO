import os
import argparse 
import yaml
import shutil

from .utils import get_component_folder 


def create_aisprint_designs(application_dir):
    ''' Create the AI-SPRINT components' designs.
        
        Steps:
        1. Create base design
        2. Run SPACE4AI-D-partitioner to create the other possible designs.
    '''

    print("Starting creating components designs..\n")

    # 1) Read DAG file
    # ----------------
    # DAG filename: 'application_dag.yaml' 
    dag_file = os.path.join(application_dir, 'common_config', 'application_dag.yaml')
    with open(dag_file, 'r') as f:
        dag_dict = yaml.safe_load(f)
    # ----------------

    # 1) Create base design
    # ---------------------
    print("- Creating base design.. ", end=' ')
    # For each component create a 'base' design
    for component_name in dag_dict['System']['components']:
        create_base_design(application_dir=application_dir,
                           component_name=component_name)

    # Initialize the component_partitions.yaml in aisprint/designs
    component_partitions = {'components': {}}
    for component_name in dag_dict['System']['components']:
        component_partitions['components'][component_name] = {}
        component_partitions['components'][component_name]['partitions'] = [component_name]
    designs_dir = os.path.join(application_dir, 'aisprint', 'designs')
    with open(os.path.join(designs_dir, 'component_partitions.yaml'), 'w') as f:
        yaml.dump(component_partitions, f)
    print("DONE.\n")
    # ---------------------

    # 2) Run partitioning tool
    # -------------------------
    print("- Finding partitions.. ", end=' ')
    # TODO: 
    # 1. Run partitionable_model manager
    # 2. Run early_exits_model manager
    # 3. Run partitioning tool which 
    #    a. Create a number of designs based on the found partitions
    #    b. Modify the component_partitions.yaml
    print("DONE.\n")
    # ---------------------------

    print("Components designs have been succesfully created in {}.".format(
        os.path.join(application_dir, 'aisprint', 'designs')))
    print("")

def create_base_design(application_dir, component_name):
    designs_dir = os.path.join(application_dir, 'aisprint', 'designs') 
    destination_dir = os.path.join(designs_dir, component_name, 'base')
    # if not os.path.exists(destination_dir):
    #     os.makedirs(destination_dir)
    
    # Get original folder name of the 'component_name'
    component_folder = get_component_folder(application_dir, component_name)

    # Copy code from the original folder to the 'component_name' design
    shutil.copytree(component_folder, destination_dir)