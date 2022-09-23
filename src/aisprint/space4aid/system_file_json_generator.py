import os
import yaml
import json
import re


global application_dir


def get_components():
    filename = "component_partitions.yaml"
    filepath = os.path.join(application_dir, component_partitions_path, filename)
    with open(filepath) as file:
        component_partitions = yaml.full_load(file)["components"]

    components = {}  # returned dict
    number_of_components = len(component_partitions)

    # cycling on numbers so that I know when I reached the end
    for i in range(number_of_components):
        component_name = list(component_partitions.keys())[i]
        components[component_name] = {}
        partitions = component_partitions[component_name]["partitions"]
        for p in partitions:  # base, partition1_1...
            if p == "base":
                memory = get_components_details(component_name)
                if i + 1 < number_of_components:
                    next_component = list(component_partitions.keys())[i + 1]
                else:  # I'm at the end of the line and there is no next
                    next_component = ""
                components[component_name]["s1"] = {component_name: {
                    "memory": memory,
                    "next": next_component,
                    "early_exit_probability": 0,
                    "data_size": 0.1
                }}
            else:
                # splitting "partition1_1" in "partition1_" and "1"
                partition, n = p.split('_')
                next_component = partition + "_" + str(int(n) + 1)
                if next_component not in partitions:
                    next_component = ""
                memory = get_components_details(component_name + "_" + p)
                # find numbers inside "partition1_1", select the first one and increment it by 1
                s_index = int(re.findall(r'\d+', p)[0]) + 1
                s = "s" + str(s_index)
                if s not in components[component_name].keys():
                    components[component_name][s] = {}
                components[component_name][s][component_name + "_" + p] = {
                    "memory": memory,
                    "next": next_component,
                    "early_exit_probability": 0,
                    "data_size": 0.1
                }

    return components


def get_components_details(name):
    filename = "candidate_deployments.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        candidate_components = yaml.full_load(file)["Components"]

    containers = []

    for c in candidate_components:
        component = candidate_components[c]
        if "partition" not in name:
            if component["name"] == name:
                containers = component["Containers"]
                break
        else:
            if "partition" in component["name"]:  # no point in checking otherwise
                # group is the first value, number is the second
                partition_group_target = re.findall(r'\d+', name)[0]
                partition_number_target = re.findall(r'\d+', name)[1]

                # component name should have only one number
                partition_number_component = re.findall(r'\d+', component["name"])[0]

                if partition_number_target == partition_number_component:  # otherwise it's not a match
                    target_name = name.strip(partition_number_target)  # removes last number
                    target_name = target_name.replace(partition_group_target, "A")  # replace first number with letter

                    component_name = component["name"].strip(partition_number_component)

                    # at this point I have ensured that the names end with "X_", or equivalent

                    if target_name[:-2] == component_name[:-2]:
                        containers = component["Containers"]
                        break

    memory = -1

    for container in containers:
        container = containers[container]
        if container["memorySize"] > memory:
            memory = container["memorySize"]

    return memory


def get_resources():
    filename = "SPACE4AI-D.yaml"
    filepath = os.path.join(application_dir, space4aid_path, filename)
    with open(filepath) as file:
        space = yaml.full_load(file)

    resources = {}
    resources_types = ["EdgeResources", "CloudResources", "FaaSResources"]

    for resources_type in resources_types:
        if resources_type in space.keys():
            resources[resources_type] = {}
            layers = space[resources_type]
            for layer_name in layers:
                resources[resources_type][layer_name] = {}
                layer = get_layer(layer_name)
                for resource in layer["Resources"]:
                    resource = layer["Resources"][resource]
                    name = resource["name"]
                    n_cores = resource["processors"]["processor1"]["computingUnits"]

                    resources[resources_type][layer_name][name] = {
                        "description": resource["description"],
                        "number": resource["totalNodes"],
                        "cost": resource["cost"],
                        "memory": resource["memorySize"],
                        "n_cores": n_cores
                    }

    return resources


def get_layer(target_layer):
    filename = "candidate_resources.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        network_domains = yaml.full_load(file)["System"]["NetworkDomains"]

    for domain_id in network_domains.keys():
        layers = network_domains[domain_id]["ComputationalLayers"].keys()
        for layer in layers:
            if layer == target_layer:
                return network_domains[domain_id]["ComputationalLayers"][layer]

    return None


def get_network():
    filename = "candidate_resources.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        network_domains = yaml.full_load(file)["System"]["NetworkDomains"]

    network_tech = {}

    for domain_id in network_domains.keys():
        access_delay = network_domains[domain_id]["AccessDelay"]
        bandwidth = network_domains[domain_id]["Bandwidth"]
        layers = get_domain_layers(domain_id)

        network_tech[domain_id] = {
            "computationallayers": layers,
            "AccessDelay": access_delay,
            "Bandwidth": bandwidth
        }

    return network_tech


def get_domain_layers(target_domain_id):
    filename = "candidate_resources.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        network_domains = yaml.full_load(file)["System"]["NetworkDomains"]

    layers = []

    for domain_id in network_domains.keys():
        if target_domain_id == domain_id:
            layers += list(network_domains[domain_id]["ComputationalLayers"].keys())
            for subdomain_id in network_domains[domain_id]["subNetworkDomains"]:
                layers += get_domain_layers(subdomain_id)

    return layers


def get_compatibility_matrix():
    filename = "component_partitions.yaml"
    filepath = os.path.join(application_dir, component_partitions_path, filename)
    with open(filepath) as file:
        components = yaml.full_load(file)["components"]

    compatibility_matrix = {}

    for component in components:
        compatibility_matrix[component] = {}
        for partition in components[component]["partitions"]:
            if partition == "base":
                resources = get_component_resources(component, "")
                compatibility_matrix[component][component] = resources
            else:
                resources = get_component_resources(component, partition)
                compatibility_matrix[component][component + "_" + partition] = resources

    # print(compatibility_matrix)

    return compatibility_matrix


def get_component_resources(target_component_name, target_partition):
    filename = "candidate_deployments.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        components = yaml.full_load(file)["Components"]

    for component_name in components.keys():
        resources = []
        component = components[component_name]

        if target_partition != "":  # if target partition not empty
            if "partition" in component["name"]:
                partition_group_target = re.findall(r'\d+', target_partition)[0]
                partition_number_target = re.findall(r'\d+', target_partition)[1]

                partition_number_component = re.findall(r'\d+', component["name"])[0]
                name = component["name"].split("_partition")[0]

                # print(target_component_name, partition_group_target, partition_number_target)
                # print(name, " ", partition_number_component)

                if target_component_name == name and partition_number_target == partition_number_component:
                    containers = component["Containers"]
                    for container_name in containers:
                        container = containers[container_name]
                        for r in container["candidateExecutionResources"]:
                            if r not in resources:
                                resources.append(r)
                    return resources

        else:
            if component["name"] == target_component_name:
                containers = component["Containers"]
                for container_name in containers:
                    container = containers[container_name]
                    for r in container["candidateExecutionResources"]:
                        if r not in resources:
                            resources.append(r)
                return resources


def get_component_name(component_id):
    filename = "candidate_deployments.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        components = yaml.full_load(file)["Components"]

    for component_name in components.keys():
        if component_name == component_id:
            return components[component_name]["name"]


def get_local_constraints():
    filename = "QoSConstraints.yaml"
    filepath = os.path.join(application_dir, space4aid_path, filename)
    with open(filepath) as file:
        constraints = yaml.full_load(file)["System"]["LocalConstraints"]

    local_constraints = {}

    for constraint in constraints:
        component_id = constraints[constraint]["componentName"]
        threshold = constraints[constraint]["threshold"]
        name = get_component_name(component_id)
        local_constraints[name] = {"local_res_time": threshold}

    return local_constraints


def get_global_constraints():
    filename = "QoSConstraints.yaml"
    filepath = os.path.join(application_dir, space4aid_path, filename)
    with open(filepath) as file:
        constraints = yaml.full_load(file)["System"]["GlobalConstraints"]

    global_constraints = {}

    for constraint in constraints:
        path_components = constraints[constraint]["pathComponents"]
        threshold = constraints[constraint]["threshold"]
        components = []
        for component_id in path_components:
            name = get_component_name(component_id)
            components.append(name)
        global_constraints[constraint] = {
            "components": components,
            "global_res_time": threshold
        }

    return global_constraints


def get_dag():
    filename = "application_dag.yaml"
    filepath = os.path.join(application_dir, common_config_path, filename)
    with open(filepath) as file:
        dependencies = yaml.full_load(file)["System"]["dependencies"]

    dag = {}

    for dependency in dependencies:
        component_a = dependency[0]
        component_b = dependency[1]
        transition_probability = dependency[2]
        if component_a not in dag.keys():
            dag[component_a] = {
                "next": [component_b],
                "transition_probability": [transition_probability],
            }
        else:
            dag[component_a]["next"].append(component_b)
            dag[component_a]["transition_probability"].append(transition_probability)

    return dag


def get_performance_models():
    filename = "performance_models.json"
    filepath = os.path.join(application_dir, oscarp_path, filename)
    with open(filepath) as file:
        data = json.load(file)

    return data


def make_system_file(directory):
    global application_dir
    application_dir = directory

    system_file = get_resources()
    system_file["Components"] = get_components()
    system_file["NetworkTechnology"] = get_network()
    system_file["CompatibilityMatrix"] = get_compatibility_matrix()
    system_file["LocalConstraints"] = get_local_constraints()
    system_file["GlobalConstraints"] = get_global_constraints()
    system_file["DirectedAcyclicGraph"] = get_dag()
    system_file["Performance"] = get_performance_models()
    system_file["Lambda"] = 0.25
    system_file["Time"] = 1

    filename = "SystemFile.json"
    filepath = os.path.join(application_dir, space4aid_path, filename)
    with open(filepath, "w") as file:
        json.dump(system_file, file, indent=4)

    return filepath


component_partitions_path = "aisprint/designs"
common_config_path = "common_config"
space4aid_path = "space4ai-d"
oscarp_path = "oscarp"


if __name__ == '__main__':
    make_system_file("Demo_project")
