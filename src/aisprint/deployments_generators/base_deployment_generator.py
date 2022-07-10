import os
import shutil

from .deployment_generator import DeploymentGenerator


class BaseDeploymentGenerator(DeploymentGenerator): 

    def __init__(self, application_dir):
        
        self.application_dir = application_dir
    
    def create_deployment(self, deployment_name, dag_filename):
        ''' Create base deployment.

            Parameters:
                - deployment_name: name of the new deployment
                - dag: application dag of the current deployment 
        '''
        super().create_deployment(deployment_name, dag_filename)

        # Copy original DAG
        shutil.copyfile(os.path.join(self.application_dir, 'common_config', 'application_dag.yaml'),
                        os.path.join(self.deployment_dir, 'application_dag.yaml'))

        # Copy tools directory
        shutil.copytree(os.path.join(self.application_dir, 'space4ai-d'), 
                        os.path.join(self.deployment_dir, 'space4ai-d'))
        shutil.copytree(os.path.join(self.application_dir, 'oscar'), 
                        os.path.join(self.deployment_dir, 'oscar'))
        shutil.copytree(os.path.join(self.application_dir, 'pycompss'), 
                        os.path.join(self.deployment_dir, 'pycompss'))
        shutil.copytree(os.path.join(self.application_dir, 'im'), 
                        os.path.join(self.deployment_dir, 'im'))
        shutil.copytree(os.path.join(self.application_dir, 'ams'), 
                        os.path.join(self.deployment_dir, 'ams'))

        # Create 'src' with symbolic links to base designs
        os.makedirs(os.path.join(self.deployment_dir, 'src'))

        designs_dir = os.path.join(
            os.path.abspath(self.application_dir), 'aisprint', 'designs')
        for component_name in self.dag_dict['System']['components']:
            source_design = os.path.join(designs_dir, component_name, 'base')
            symlink = os.path.join(
                os.path.abspath(self.deployment_dir), 'src', component_name)
            os.symlink(source_design, symlink)

        # Initialize the symbolic link to the optimal deployment to point 
        # to the base deployment
        source_deployment = os.path.join(
            os.path.abspath(self.application_dir), 'aisprint', 'deployments', deployment_name)
        current_design_symlink = os.path.join(
            os.path.abspath(self.application_dir), 'aisprint', 'deployments', 'optimal_deployment')
        os.symlink(source_deployment, current_design_symlink)
        print("Current deployment is '{}'.\n".format(deployment_name))
    