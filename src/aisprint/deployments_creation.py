import os
import yaml
import shutil

from .utils import run_annotation_managers, AISPRINT_ANNOTATIONS
from .annotations import annotation_managers


def create_aisprint_deployments(application_dir):
    ''' Create AI-SPRINT candidate deployments and run annotation managers 
        to create configuration files based on the parsed annotations and the
        DAG specific of the deployments.

        # TODO: at the current stage only the 'base' deployments is created.
        # The SPACE4AI-D-partitioner will be in charge of defining the other deployments.
    '''

    print("Starting creating candidate AI-SPRINT deployments..")

    # 1) Create deployments
    # ---------------------
    # Create deployment referring to 'base' design
    # NOTE: the DAG file is a copy of the original one for the 'base' design
    with open(os.path.join(application_dir, 'application_dag.yaml'), 'r') as f:
        original_dag = yaml.safe_load(f) 
    create_new_deployment(application_dir=application_dir,
                          deployment_name='base', dag=original_dag)
    # NOTE: Set current deployment as the 'base' one by default. 
    # It can change after SPACE4AI-D.
    assign_current_deployment(application_dir=application_dir, deployment_name='base') 

    # ---------------------
    
    # 2) Run annotation managers for each deployment
    # ----------------------------------------------
    
    # Create annotation managers
    annotation_managers_dict = {}
    for aisprint_annotation in AISPRINT_ANNOTATIONS:
        if aisprint_annotation == 'annotation':
            continue
        manager_module_name = aisprint_annotation + '_manager'
        manager_class_name = "".join([s.capitalize() for s in manager_module_name.split('_')])
        manager_class = getattr(annotation_managers, manager_class_name)
        annotation_managers_dict[aisprint_annotation] = manager_class(
            application_name=original_dag['System']['name'], application_dir=application_dir)

    # Run annotation managers for each deployment
    deployments_dir = os.path.join(application_dir, 'aisprint', 'deployments')
    deployments_names = next(os.walk(deployments_dir))[1]

    print("Generating configuration files for each deployment based on the found AI-SPRINT annotations..", end=' ')
    for deployment_name in deployments_names:
        run_annotation_managers(annotation_managers=annotation_managers_dict, 
                                deployment_name=deployment_name)
    print("DONE.\n")
    # ----------------------------------------------

def create_new_deployment(application_dir, deployment_name, dag):
    deployments_dir=os.path.join(application_dir, 'aisprint', 'deployments')
    destination_dir = os.path.join(deployments_dir, deployment_name)
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    with open(os.path.join(destination_dir, 'application_dag.yaml'), 'w') as f:
        yaml.dump(dag, f, default_flow_style=None)

    shutil.copytree(os.path.join(application_dir, 'space4ai-d'), 
                    os.path.join(destination_dir, 'space4ai-d'))
    shutil.copytree(os.path.join(application_dir, 'oscar'), 
                    os.path.join(destination_dir, 'oscar'))
    shutil.copytree(os.path.join(application_dir, 'pycompss'), 
                    os.path.join(destination_dir, 'pycompss'))
    shutil.copytree(os.path.join(application_dir, 'im'), 
                    os.path.join(destination_dir, 'im'))
    shutil.copytree(os.path.join(application_dir, 'ams'), 
                    os.path.join(destination_dir, 'ams'))

    print("- New deployment '{}' created.".format(deployment_name))

def assign_current_deployment(application_dir, deployment_name):
    source_deployment = os.path.join(
        os.path.abspath(application_dir), 'aisprint', 'deployments', deployment_name)
    current_design_symlink = os.path.join(
        os.path.abspath(application_dir), 'current_deployment')
    os.symlink(source_deployment, current_design_symlink)
    print("Current deployment is '{}'.\n".format(deployment_name))