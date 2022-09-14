import yaml


def get_resources(work_dir):
    resources = {
        "RasPi": {
            "oscarcli_alias": "oscar-raspi",
            "minio_alias": "minio-raspi",
            "ssh": "grycap@158.42.105.64/10022",
            "total_nodes": 3,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 4096
        },
        "VM1": {
            "oscarcli_alias": "oscar-vm",
            "minio_alias": "minio-vm",
            "ssh": "aisprint@158.42.105.149/10022",
            "total_nodes": 8,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 8192
        },
        "VM2": {
            "oscarcli_alias": "oscar-vm",
            "minio_alias": "minio-vm",
            "ssh": "aisprint@158.42.105.149/10022",
            "total_nodes": 8,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 8192
        },
        "VM3": {
            "oscarcli_alias": "oscar-vm",
            "minio_alias": "minio-vm",
            "ssh": "aisprint@158.42.105.149/10022",
            "total_nodes": 8,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 8192
        },
    }
    return resources


def get_components_and_images(work_dir):
    with open(work_dir + "common_config/candidate_deployments.yaml") as file:
        candidate_deployments = yaml.load(file, Loader=yaml.Loader)

    components = {}
    images = {}

    for component_key in candidate_deployments["Components"]:
        component = candidate_deployments["Components"][component_key]
        name = component["name"]
        short_id = shorten_key(component_key)  # C1
        component_resources = []

        if "partition" not in name:
            for container_key in component["Containers"]:
                container = component["Containers"][container_key]
                image = container["image"]
                resources = container["candidateExecutionResources"]
                component_resources += resources

                for r in resources:
                    full_id = short_id + "@" + r  # C1@VM1
                    images[full_id] = image

            components[component_key] = {
                "name": name,
                "resources": component_resources  # todo duplicated items?
            }

        else:
            target, matches = get_correct_partition(work_dir, component)
            target_string = "partition" + target

            for m in matches:
                for container_key in component["Containers"]:
                    container = component["Containers"][container_key]
                    image = container["image"]
                    resources = container["candidateExecutionResources"]
                    component_resources += resources

                    match_string = "partition" + str(m)

                    for r in resources:
                        full_id = short_id.replace(target, m) + "@" + r  # C1@VM1
                        images[full_id] = image.replace(target, m)

                components[component_key.replace(target, m)] = {
                    "name": name.replace(target_string, match_string),
                    "resources": component_resources  # todo duplicated items?
                }

    return components, images


def get_correct_partition(work_dir, component):
    with open(work_dir + "aisprint/designs/component_partitions.yaml") as file:
        component_partitions = yaml.load(file, Loader=yaml.Loader)["components"]

    name, partition = component["name"].split("-partition")

    partitions = component_partitions[name]["partitions"]
    matches = []
    for p in partitions:
        if p[-1] == partition[-1]:
            matches.append(p[-3])

    return partition[0], matches


def get_run_parameters(work_dir):
    with open(work_dir + "oscarp/run_parameters.yaml") as file:
        run_parameters = yaml.load(file, Loader=yaml.Loader)

    return run_parameters["run_parameters"]


# todo until node labelling is implemented, this is useless
def get_testing_parameters():
    testing_parameters = {
        "component1": {
            "parallelism": [],
        },
        "component2": {
            "parallelism": [],
        },
        "component3": {
            "parallelism": [],
        },
        "component4": {
            "parallelism": [],
        },
        "component5": {
            "parallelism": [],
        },
        "component6": {
            "parallelism": [],
        }
    }
    return testing_parameters


# todo until node labelling is implemented, this is also useless
# todo add check to ensure that lists are fully joinable
# merges the components with the testing parameters, as to have everything in one place
def get_testing_components(components, testing_parameters):
    testing_components = {}

    """
    for c in components.keys():
        for t in testing_parameters.keys():
            if c == t:
                short_id = shorten_key(c)
                for r in components[c]["resources"]:
                    full_id = short_id + "@" + r
                    testing_components[full_id] = {
                        "name": components[c]["name"],
                        "parallelism": testing_parameters[t]
                    }
    """

    for c in components.keys():
        short_id = shorten_key(c)
        for r in components[c]["resources"]:
            full_id = short_id + "@" + r
            testing_components[full_id] = {
                "name": components[c]["name"],
                "parallelism": "",
            }

    return testing_components


def shorten_key(name):
    if "partition" in name:
        c, p, i = name.split("_")
        c = c.strip("component")
        p = p.strip("partition")
        return "C" + str(c) + "P" + str(p) + "." + str(i)
    else:
        c = name.strip("component")
        return "C" + str(c)
