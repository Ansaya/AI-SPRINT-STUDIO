import os
import yaml
import json

global application_dir


def parse_output_json():
    filename = "Output.json"
    filepath = os.path.join(application_dir, space4aid_path, filename)
    with open(filepath) as file:
        data = json.load(file)

    c_keys = data["components"].keys()
    # print(c_keys)

    components_values = []

    for c in c_keys:
        s_keys = data["components"][c].keys()
        # print(s_keys)
        for s in s_keys:
            if type(data["components"][c][s]) is dict:
                h_keys = data["components"][c][s].keys()
                # print(h_keys)
                for h in h_keys:
                    computational_layer = data["components"][c][s][h]
                    components_values.append((h, computational_layer))

    # print("Components values: ", components_values)
    return components_values


def find_right_components(components_values):
    filename = "candidate_deployments.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        deployments = yaml.full_load(file)

    # print(components_values)

    d_keys = deployments["Components"].keys()

    components = {}

    for component_values in components_values:
        # c = component_values[0]  # c1
        h = component_values[0]  # h1
        # c = c.replace("c", "component")  # component1
        # h = int(h.replace("h", ""))  # 1

        for d in d_keys:  # [ component1, component1_partitionX_1, ... ]
            comp_name = deployments["Components"][d]["name"]
            # print(deployments["Components"][d]["name"])
            # print(h)

            if comp_name[:-3] == h[:-3] and comp_name[-1] == h[-1]:
                components[h] = update_component(deployments["Components"][d], component_values[1], h)
                break

    # components = {"Components": components}

    return components


def update_component(old_component, layer_info, name):
    # copies component body from candidate_deployments.yaml
    new_component = old_component

    # fix name
    new_component["name"] = name

    # rename layer key and puts in the correct value
    computational_layer = list(layer_info.keys())[0]
    exec_layer = int(computational_layer.replace("computationalLayer", ""))
    new_component.pop("candidateExecutionLayers")
    new_component["executionLayer"] = exec_layer

    # choose right container
    containers = old_component["Containers"]

    # picks the correct resource from Output.json
    chosen_resource = list(layer_info[computational_layer].keys())[0]

    # if there's only one container, job done
    if len(containers.keys()) == 1:
        key = list(containers.keys())[0]

    # else find the right one
    else:
        for key in containers.keys():

            # if there's a match we found our container
            # no error control if no match found, assuming not possible
            if chosen_resource in containers[key]["candidateExecutionResources"]:
                break

    # select correct container and rename key
    chosen_container = containers[key]
    chosen_container.pop("candidateExecutionResources")
    chosen_container["selectedExecutionResource"] = chosen_resource

    # save correct container in component
    new_component["Containers"] = {"container1": chosen_container}

    return new_component


def find_right_resources(layers):
    filename = "candidate_resources.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        candidate_resources = yaml.full_load(file)["System"]

    net_domains = candidate_resources["NetworkDomains"].keys()

    comp_layer_resource_tuple = []

    # this associates the valid components from output.json to the one from candidate_resources.yaml
    for layer in layers:
        computational_layer = list(layer[1].keys())[0]
        resource = list(layer[1][computational_layer].keys())[0]

        comp_layer_resource_tuple.append((computational_layer, resource))

    # print(comp_layer_resource_tuple)
    to_pop = []

    for n in net_domains:
        n_keys = candidate_resources["NetworkDomains"][n].keys()
        if "ComputationalLayers" in n_keys:
            computational_layers = candidate_resources["NetworkDomains"][n]["ComputationalLayers"]
            cl_keys = computational_layers.keys()
            # print(cl_keys)
            for cl in cl_keys:
                resources_keys = computational_layers[cl]["Resources"].keys()
                for r in resources_keys:
                    resource = computational_layers[cl]["Resources"][r]["name"]
                    # print((cl, resource))
                    # if not a winner component, pop
                    if (cl, resource) not in comp_layer_resource_tuple:
                        # print("popped")
                        to_pop.append([n, cl, r])
                    # otherwise, make sure that it has the correct number of nodes
                    else:
                        index = comp_layer_resource_tuple.index((cl, resource))
                        if "number" in layers[index][1][cl][resource].keys():
                            correct_node_number = layers[index][1][cl][resource]["number"]
                            computational_layers[cl]["Resources"][r]["totalNodes"] = correct_node_number

    for array in to_pop:
        n = array[0]
        cl = array[1]
        r = array[2]

        candidate_resources["NetworkDomains"][n]["ComputationalLayers"][cl]["Resources"].pop(r)

    return fix_resources(candidate_resources)


def fix_resources(candidate_resources):
    # If layer has no more resources, delete layer #
    # otherwise fix resources number to fill gaps
    to_pop = []
    net_domains = candidate_resources["NetworkDomains"].keys()
    for n in net_domains:
        n_keys = candidate_resources["NetworkDomains"][n].keys()
        if "ComputationalLayers" in n_keys:
            computational_layers = candidate_resources["NetworkDomains"][n]["ComputationalLayers"]
            cl_keys = computational_layers.keys()
            # print(cl_keys)
            for cl in cl_keys:
                resources = computational_layers[cl]["Resources"]
                resources_keys = list(resources.keys())
                if len(resources_keys) == 0:
                    to_pop.append([n, cl])
                else:
                    for i in range(0, len(resources_keys)):
                        if resources_keys[i] != "resource" + str(i + 1):
                            resources["resource" + str(i + 1)] = resources.pop(resources_keys[i])
                            # print(resources_keys[i])

    for array in to_pop:
        n = array[0]
        cl = array[1]

        candidate_resources["NetworkDomains"][n]["ComputationalLayers"].pop(cl)

    # if net domain has no more layers, delete domain
    to_pop = []
    net_domains = candidate_resources["NetworkDomains"].keys()
    no_comp_layers_domains = []
    for n in net_domains:
        n_keys = candidate_resources["NetworkDomains"][n].keys()
        if "ComputationalLayers" in n_keys:
            computational_layers = candidate_resources["NetworkDomains"][n]["ComputationalLayers"]
            cl_keys = computational_layers.keys()
            if len(cl_keys) == 0:
                to_pop.append(n)
        else:
            no_comp_layers_domains.append(n)

    for n in to_pop:
        candidate_resources["NetworkDomains"].pop(n)

    # at this point all NDs have either valid comp_layers or none
    # if they have no comp_layers and no valid subdomains, delete domain
    net_domains = set(candidate_resources["NetworkDomains"].keys())
    net_domains -= set(no_comp_layers_domains)

    for n in no_comp_layers_domains:
        sub_nd = candidate_resources["NetworkDomains"][n]["subNetworkDomains"]
        valid_sub_nds = []
        for s in sub_nd:
            if s in net_domains:
                valid_sub_nds.append(s)

        # if not empty
        if valid_sub_nds:
            candidate_resources["NetworkDomains"][n]["subNetworkDomains"] = valid_sub_nds
        else:
            to_pop.append(n)

    for n in to_pop:
        candidate_resources["NetworkDomains"].pop(n)

    return candidate_resources


def make_output_yaml(components, resources):
    output = {"System": {
        "Components": components,
        "Resources": resources
    }}

    filename = "production_deployment.yaml"
    filepath = os.path.join(application_dir, space4aid_path, filename)
    with open(filepath, "w") as file:
        yaml.dump(output, file, sort_keys=False)


def main(directory):
    global application_dir
    application_dir = directory

    # extracts useful info from output_json
    component_values = parse_output_json()
    # picks the correct components
    final_components = find_right_components(component_values)
    # picks the correct resources
    final_resources = find_right_resources(component_values)
    # puts them together in the output.yaml file
    make_output_yaml(final_components, final_resources)


component_partitions_path = "aisprint/designs"
common_config_path = "common_config"
space4aid_path = "space4ai-d"


if __name__ == '__main__':
    main("Demo_project")
