import copy
import time

from input_files_parser import get_resources, get_run_parameters, get_components_and_images, get_testing_components
from deployment_generator import get_testing_units, get_deployments, reorder_deployments, \
    get_single_services_from_deployment, make_deployments_summary
from run_coordinator import make_oscar_p_input_file
from oscarp.utils import auto_mkdir

import oscarp.oscarp as oscarp


def main(work_dir):

    if work_dir[-1] != "/":
        work_dir += "/"

    oscarp.executables.init(work_dir + "oscarp/")

    # get the necessary info from the different input file
    resources = get_resources(work_dir)
    components, images = get_components_and_images(work_dir)
    run_parameters = get_run_parameters(work_dir)
    # testing_parameters = get_testing_parameters()
    testing_parameters = None

    # merge some of those info together (check graph in coordinator.png)
    testing_components = get_testing_components(components, testing_parameters)
    testing_units = get_testing_units(testing_components)

    # create list of deployments, rearrange them as necessary
    deployments = get_deployments(testing_units)
    deployments = reorder_deployments(deployments, resources)

    # set the stage for the campaign
    campaign_dir = work_dir + "oscarp/" + run_parameters["run"]["campaign_dir"] + "/"
    auto_mkdir(campaign_dir)
    # auto_mkdir(campaign_dir + "/deployments/")
    make_deployments_summary(campaign_dir, deployments)

    tested_services = []

    for i in range(len(deployments)):
        d = deployments[i]

        print("\nTesting deployment_" + str(i) + ":")

        # todo this will all be wrapped in a for loop, with IM correcting the cluster at every iteration

        run_parameters["run"]["campaign_dir"] = campaign_dir
        run_parameters["run"]["run_name"] = "deployment_" + str(i)
        current_deployment_dir = campaign_dir + "deployment_" + str(i)

        make_oscar_p_input_file(d, testing_components, resources, copy.deepcopy(run_parameters), images,
                                is_single_service=False, service_number=0)

        oscarp.main(clean_buckets=True)

        auto_mkdir(current_deployment_dir + "/single_services/")

        services_in_deployment, services_to_test, tested_services = get_single_services_from_deployment(d, tested_services)

        print("\nTesting services of deployment_" + str(i) + ":")

        for j in range(len(services_in_deployment)):
            s = services_in_deployment[j]
            if s in services_to_test:
                run_parameters["run"]["campaign_dir"] = current_deployment_dir + "/single_services"
                run_parameters["run"]["run_name"] = s[0]

                make_oscar_p_input_file(s, testing_components, resources, copy.deepcopy(run_parameters), images,
                                        is_single_service=True, service_number=j)
                oscarp.main()
                print()

        time.sleep(5)


if __name__ == '__main__':
    main("Demo_project")
