from itertools import combinations


# # # # # # # # # # # #
# Main functions
# # # # # # # # # # # #

def get_testing_units(testing_components):

    testing_units = []
    g = 1
    while True:
        current_group = []
        group = query_testing_components(testing_components, g, None, None)

        # if there are no more matches, exits
        if not group:
            break

        for c in group:
            # if it's a partition, I compose the unit by connecting all matching partitions
            if is_partition(c):
                current_group += connect_partitions(testing_components, c)
            else:
                current_group.append([c])

        testing_units.append(current_group)
        g += 1

    """
    for g in testing_units:
        for u in g:
            print(u)
        print("")
    """

    return testing_units


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


def get_deployments(units):
    deployments = units[0]

    for i in range(1, len(units)):
        temp_list = []

        for x in deployments:
            for u in units[i]:
                n = x + u
                temp_list.append(n)

        deployments = temp_list

    """
    for d in deployments:
        print(d)
    """

    return deployments


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

    # reordered_deployments = add_single_services(reordered_deployments)

    return reordered_deployments


def get_single_services_from_deployment(deployment, tested_services):

    services_in_deployment = []
    services_to_test = []

    for c in deployment:
        services_in_deployment.append([c])
        if [c] not in tested_services:
            services_to_test.append([c])

    tested_services += services_to_test

    return services_in_deployment, services_to_test, tested_services


def make_deployments_summary(campaign_dir, deployments):
    print("Deployments:")
    with open(campaign_dir + "/deployments_summary.txt", "w") as file:
        for i in range(len(deployments)):
            deployment = "deployment_" + str(i) + ": " + str(deployments[i])
            print("\t" + deployment)
            file.write(deployment + "\n")


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

