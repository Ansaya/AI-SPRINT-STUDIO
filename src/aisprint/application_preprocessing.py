import os
import yaml
import shutil

from .utils import get_component_folder 


class ApplicationPreprocessor():

    def __init__(self, application_dir):
        
        self.application_dir = application_dir

    def create_base_design(self):
        ''' Create the base design and initialize the component partitions file.
        '''

        # Read DAG file
        # ----------------
        # DAG filename: 'application_dag.yaml' 
        dag_file = os.path.join(self.application_dir, 'common_config', 'application_dag.yaml')
        with open(dag_file, 'r') as f:
            dag_dict = yaml.safe_load(f)
        # ----------------

        # Create base design
        # ---------------------
        print("- Creating base designs..\n")
        designs_dir = os.path.join(self.application_dir, 'aisprint', 'designs') 
        # For each component create a 'base' design
        for component_name in dag_dict['System']['components']:
            destination_dir = os.path.join(designs_dir, component_name, 'base')
            
            # Get original folder name of the 'component_name'
            component_folder = get_component_folder(self.application_dir, component_name)

            # Copy code from the original folder to the 'component_name' design
            shutil.copytree(component_folder, destination_dir)

        # Initialize the component_partitions.yaml in aisprint/designs
        print("Initializing component_partitions.yaml..", end=' ')
        component_partitions = {'components': {}}
        for component_name in dag_dict['System']['components']:
            component_partitions['components'][component_name] = {}
            component_partitions['components'][component_name]['partitions'] = [component_name]
        designs_dir = os.path.join(self.application_dir, 'aisprint', 'designs')
        with open(os.path.join(designs_dir, 'component_partitions.yaml'), 'w') as f:
            yaml.dump(component_partitions, f)
        print("DONE.\n")
        # ---------------------