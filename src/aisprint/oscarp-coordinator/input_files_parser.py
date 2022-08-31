import yaml


def get_resources():
    resources = {
        "RasPi": {
            "oscarcli_alias": "oscar-raspi",
            "minio_alias": "minio-raspi",
            "ssh": "grycap@158.42.105.64/10022",
            "total_nodes": 3,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 4096
        },
        "VM": {
            "oscarcli_alias": "oscar-vm",
            "minio_alias": "minio-vm",
            "ssh": "aisprint@158.42.105.149/10022",
            "total_nodes": 8,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 8192
        },
        "AWS": {
            "oscarcli_alias": "oscar-aws",
            "minio_alias": "minio-aws",
            "ssh": None,
            "total_nodes": 8,
            "max_cpu_cores": 4.0,
            "max_memory_mb": 8192
        }
    }
    return resources


def get_components():
    components = {
        "component1": {
            "name": "ffmpeg0",
            "resources": ["VM"],
        },
        "component2": {
            "name": "librosa",
            "resources": ["VM"],
        },
        "component3": {
            "name": "ffmpeg1",
            "resources": ["RasPi"],
        },
        "component4": {
            "name": "ffmpeg2",
            "resources": ["VM"],
        },
        "component5": {
            "name": "deepspeech",
            "resources": ["AWS"],
        },
        "component6": {
            "name": "ubuntu",
            "resources": ["AWS"],
        }
    }

    return components


def get_components_and_images():
    with open("input-files/candidate_deployments.yaml") as file:
        candidate_deployments = yaml.load(file, Loader=yaml.Loader)

    components = {}
    images = {}

    for component_key in candidate_deployments["Components"]:
        component = candidate_deployments["Components"][component_key]
        name = component["name"]
        short_id = shorten_key(component_key)  # C1
        component_resources = []

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
            "resources": component_resources
        }

    return components, images


def get_run_parameters():
    with open("input-files/run_parameters.yaml") as file:
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


# todo add check to ensure that lists are fully joinable
# todo until node labelling is implemented, this is also useless
# merges the components with the testing parameters, as to have everything in one place
def get_testing_components(components, testing_parameters):
    testing_components = {}

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
