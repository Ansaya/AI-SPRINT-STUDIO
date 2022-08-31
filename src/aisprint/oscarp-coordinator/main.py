from input_files_parser import get_resources, get_components, \
    get_run_parameters, get_components_and_images, get_testing_parameters, get_testing_components
from deployment_generator import get_testing_units, get_deployments, reorder_deployments, \
    get_single_services_from_deployment, make_deployments_summary
from run_coordinator import make_oscar_p_input_file
from oscarp.utils import auto_mkdir

import oscarp.main as oscarp


def main():

    # get the necessary info from the different input file
    resources = get_resources()
    components, images = get_components_and_images()
    run_parameters = get_run_parameters()
    testing_parameters = get_testing_parameters()

    # merge some of those info together (check graph in coordinator.png)
    testing_components = get_testing_components(components, testing_parameters)
    testing_units = get_testing_units(testing_components)

    # create list of deployments, rearrange them as necessary
    deployments = get_deployments(testing_units)
    deployments = reorder_deployments(deployments, resources)

    # set the stage for the campaign
    campaign_dir = run_parameters["run"]["campaign_dir"]
    auto_mkdir(campaign_dir)
    auto_mkdir(campaign_dir + "/deployments/")
    auto_mkdir(campaign_dir + "/single_services/")
    make_deployments_summary(campaign_dir, deployments)

    tested_services = []

    for i in range(len(deployments)):
        d = deployments[i]

        print("\nTesting deployment " + str(i) + ":")

        run_parameters["run"]["campaign_dir"] = campaign_dir + "/deployments"
        run_parameters["run"]["run_name"] = "deployment_" + str(i)

        make_oscar_p_input_file(d, testing_components, resources, run_parameters, images,
                                is_single_service=False, service_number=0)

        oscarp.main(clean_buckets=True)

        # todo all this stuff should not be necessary, if already tested OSCAR-P skips it on its own
        services_in_deployment, _, _ = get_single_services_from_deployment(d, tested_services)

        services_to_test = [["C5@AWS"], ["C6@AWS"]]  # todo remove, this is temporary to reduce AWS usage
        # services_to_test = [["C1@VM"], ["C2@VM"], ["C3@RasPi"], ["C4@VM"]]  # todo remove too

        for j in range(len(services_in_deployment)):
            s = services_in_deployment[j]
            if s in services_to_test:  # todo remove if, this is temporary to reduce AWS usage
                run_parameters["run"]["campaign_dir"] = campaign_dir + "/single_services"
                run_parameters["run"]["run_name"] = s[0]

                make_oscar_p_input_file(s, testing_components, resources, run_parameters, images,
                                        is_single_service=True, service_number=j)
                oscarp.main()


if __name__ == '__main__':
    main()
