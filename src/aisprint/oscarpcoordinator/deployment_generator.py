import math
from itertools import combinations

from oscarp.utils import show_fatal_error

import global_parameters as gp


# # # # # # # # # # # #
# Main functions
# # # # # # # # # # # #

def get_testing_units():

    testing_units = []
    g = 1
    while True:
        current_group = []
        group = query_testing_components(gp.testing_components, g, None, None)

        # if there are no more matches, exits
        if not group:
            break

        for c in group:
            # if it's a partition, I compose the unit by connecting all matching partitions
            if is_partition(c):
                current_group += connect_partitions(gp.testing_components, c)
            else:
                current_group.append([c])

        testing_units.append(current_group)
        g += 1

    gp.testing_units = testing_units


def connect_partitions(testing_components, component):
    c, p, i, r = get_testing_component_values(component)
    i = int(i)

    if i > 1:
        return []

    connected_partitions = [[component]]

    # print("component", component)

    while True:
        i += 1

        # print("before", connected_partitions)
        # print("query", c, p, i)
        matching_partitions = query_testing_components(testing_components, c, p, i)
        # print("matches", matching_partitions)
        if not matching_partitions:
            break

        temp_list = []
        for x in connected_partitions:
            for m in matching_partitions:
                temp_list.append(x + [m])
        connected_partitions = temp_list

        # print("after", connected_partitions)

    return connected_partitions


def get_deployments():
    deployments = gp.testing_units[0]

    for i in range(1, len(gp.testing_units)):
        temp_list = []

        for x in deployments:
            for u in gp.testing_units[i]:
                n = x + u
                temp_list.append(n)

        deployments = temp_list

    gp.deployments = deployments


def reorder_deployments(deployments, resources):
    reordered_deployments = []

    combined_resources = get_resources_combinations(resources)

    for c in combined_resources:
        for d in deployments:
            used_resources = get_used_resources(d)
            if check_match_combined_used_resources(c, used_resources):
                reordered_deployments.append(d)

        for r in reordered_deployments:
            if r in deployments:
                deployments.remove(r)

    return reordered_deployments


def get_single_services_from_deployment():

    services_in_deployment = []
    services_to_test = []

    for c in gp.current_deployment:
        services_in_deployment.append(c)
        if c not in gp.tested_services:
            services_to_test.append(c)

    gp.tested_services += services_to_test

    return services_in_deployment, services_to_test


def make_deployments_summary():
    print("Deployments:")
    with open(gp.campaign_dir + "/deployments_summary.txt", "w") as file:
        for i in range(len(gp.deployments)):
            deployment = "deployment_" + str(i) + ": " + str(gp.deployments[i])
            print("\t" + deployment)
            file.write(deployment + "\n")


def make_cluster_requirements():
    cluster_requirements = {}
    for component in gp.current_deployment:
        resource = component.split('@')[1]
        parallelism = gp.testing_components[component]["parallelism"]
        # container requirements
        cpu = gp.images[component]["cpu"]
        memory = gp.images[component]["memory"]
        # node resources (minus 10% headroom for OS)
        node_cpu = gp.resources[resource]["max_cpu_cores"] * 0.9
        node_memory = gp.resources[resource]["max_memory_mb"] * 0.9
        total_nodes = gp.resources[resource]["total_nodes"]

        # make sure that a node can fit at least one container
        if cpu > node_cpu or memory > node_memory:
            show_fatal_error("Container requires more resources than available on a node")

        if resource == "AWS Lambda" and gp.images[component]["memory"] > 3008:
            show_fatal_error("Memory for Lambda functions can't exceed 3008 MB")

        # calculate how many containers can a node accommodate
        container_per_node = math.floor(min(node_cpu / cpu, node_memory / memory))
        node_per_container = 1 / container_per_node

        node_requirements = []

        if resource not in cluster_requirements.keys():
            for x in parallelism:
                nr = math.ceil(x * node_per_container)
                node_requirements.append(nr)
                if nr > total_nodes:
                    show_fatal_error("A parallelism of {} isn't possible on resource {}"
                                     .format(x, resource))
        else:
            prev_node_requirements = cluster_requirements[resource]["nodes"]
            for x in range(len(parallelism)):
                nr = math.ceil(parallelism[x] * node_per_container)  # node requirement for current parallelism
                nr += prev_node_requirements[x]  # node requirement for current parallelism, for all services up to now
                node_requirements.append(nr)
                if nr > total_nodes:
                    show_fatal_error("Resource {} has {} nodes, but {} are needed for testing"
                                     .format(resource, total_nodes, nr))

        cluster_requirements[resource] = {
            "nodes": node_requirements
        }

    gp.clusters_node_requirements = cluster_requirements
    return


# # # # # # # # # # # #
# Secondary functions
# # # # # # # # # # # #

def query_testing_components(testing_components, c, p, i):
    matches = []

    target_component = get_testing_component_name(c, p, i)

    for t in testing_components.keys():
        if target_component in t:
            matches.append(t)

    return matches


def get_testing_component_name(c, p, i):
    if p is None:
        return "C" + str(c)
    elif i is None:
        return "C" + str(c) + "P" + str(p)
    else:
        return "C" + str(c) + "P" + str(p) + "." + str(i)


def get_testing_component_values(name):
    if is_partition(name):
        c, r = name.split("@")
        c, p = c.split("P")
        c = c.strip("C")
        p, i = p.split(".")
        return c, p, i, r
    else:
        c, r = name.split("@")
        c = c.strip("C")
        return c, None, None, r


def is_partition(name):
    c = name.split("@")[0]
    if "P" in c:
        return True
    else:
        return False


def get_used_resources(deployment):
    used_resources = []

    for d in deployment:
        _, _, _, r = get_testing_component_values(d)
        if r not in used_resources:
            used_resources.append(r)

    return used_resources


def get_resources_combinations(resources):
    resources = list(resources.keys())

    combined_resources = []

    for i in range(1, len(resources) + 1):
        combined_resources += list(combinations(resources, i))

    return combined_resources


def check_match_combined_used_resources(combined_resources, used_resources):

    # if they have different sizes they're not identical
    if len(combined_resources) != len(used_resources):
        return False

    # if they have the same size, check that every item in combined appears in used
    for c in combined_resources:
        if c not in used_resources:
            return False

    return True

