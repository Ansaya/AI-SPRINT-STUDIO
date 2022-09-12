# this file includes functions that print out content
import os.path

from termcolor import colored

from input_file_processing import get_debug, get_closest_parallelism_level
from utils import append_string_to_file, strip_ansi_from_string, create_new_file

global summary_filepath


# given two runs, it shows the difference in cpu and memory settings
def runs_diff_services(run1, run2):

    print("\t\tServices:")
    append_to_deployment_summary("\t\tServices:")
    for i in range(len(run1["services"])):
        s1 = run1["services"][i]
        s2 = run2["services"][i]
        service_name = "{:<20}".format(s1["name"])

        output = ""
        if s1["cpu"] != s2["cpu"]:
            output += "cpu: " + colored(s1["cpu"], "green") + " -> " + colored(s2["cpu"], "green")
            output += ", memory: " + colored(s1["memory"], "green") + " mb -> " + colored(s2["memory"], "green") + " mb"

        if output != "":
            show_and_save_to_summary("\t\t\t" + colored(service_name, "blue") + output)
        else:
            show_and_save_to_summary("\t\t\t" + colored(service_name, "blue") + colored("unchanged", "green"))

        output = ""
        if s1["cluster"] != s2["cluster"]:
            output += "cluster: " + colored(s1["cluster"], "green") + " -> " + colored(s2["cluster"], "green")

        if output != "":
            show_and_save_to_summary("\t\t\t" + colored(service_name, "blue") + output)


def runs_diff_clusters(last_parallelism, run, clusters):
    current_parallelism = run["parallelism"]

    show_and_save_to_summary("\t\tClusters:")
    for cluster_name in clusters:
        cluster = clusters[cluster_name]
        old_closest_parallelism = get_closest_parallelism_level(last_parallelism,
                                                                cluster["possible_parallelism"], cluster_name, False)
        new_closest_parallelism = get_closest_parallelism_level(current_parallelism,
                                                                cluster["possible_parallelism"], cluster_name, False)
        old_nodes = cluster["possible_parallelism"][old_closest_parallelism][1]
        new_nodes = cluster["possible_parallelism"][new_closest_parallelism][1]
        cluster_name = "{:<20}".format(cluster_name)

        output = ""
        if old_nodes != new_nodes:
            output += "nodes: " + colored(old_nodes, "green") + " -> " + colored(new_nodes, "green")

        if output != "":
            show_and_save_to_summary("\t\t\t" + colored(cluster_name, "blue") + output)
        else:
            show_and_save_to_summary("\t\t\t" + colored(cluster_name, "blue") + colored("unchanged", "green"))

    return current_parallelism


def show_all_services(run):
    show_and_save_to_summary("\t" + run["id"] + " - Parallelism level: " + str(run["parallelism"]))
    show_and_save_to_summary("\t\tServices:")

    for s in run["services"]:
        service_name = "{:<20}".format(s["name"])
        show_and_save_to_summary("\t\t\t" + colored(service_name, "blue")
              + "cpu: " + colored(s["cpu"], "green")
              + " , memory: " + colored(s["memory"], "green") + " mb"
              + " , cluster: " + colored(s["cluster"], "green"))

    return


def show_all_clusters(run, clusters):
    show_and_save_to_summary("\t\tClusters:")
    requested_parallelism = run["parallelism"]

    for cluster_name in clusters:
        cluster = clusters[cluster_name]
        closest_parallelism = get_closest_parallelism_level(requested_parallelism,
                                                            cluster["possible_parallelism"], cluster_name, False)
        nodes = cluster["possible_parallelism"][closest_parallelism][1]
        cluster_name = "{:<20}".format(cluster_name)
        show_and_save_to_summary("\t\t\t" + colored(cluster_name, "blue") + "nodes: " + colored(str(nodes), "green"))

    return requested_parallelism


# todo add total number of runs
def show_runs(base, repetitions, clusters, run_dir):
    global summary_filepath
    summary_filepath = os.path.join(run_dir, "campaign_summary.txt")
    create_new_file(summary_filepath)
    show_and_save_to_summary("\nScheduler:")
    show_all_services(base[0])
    last_parallelism = show_all_clusters(base[0], clusters)
    show_and_save_to_summary("")

    for i in range(1, len(base)):
        show_and_save_to_summary("\t" + base[i]["id"] + " - Parallelism level: " + str(base[i]["parallelism"]))
        runs_diff_services(base[i-1], base[i])
        last_parallelism = runs_diff_clusters(last_parallelism, base[i], clusters)
        show_and_save_to_summary("")

    show_and_save_to_summary("\n\tRepeated " + colored(str(repetitions), "green") + " time(s), "
          + str(len(base) * repetitions) + " runs in total")

    # todo re-enable this after testing!
    # value = get_valid_input("Do you want to proceed? (y/n)\t", ["y", "n"])
    # print()  # just for spacing
    value = "y"

    if value == "n":
        print(colored("Exiting...", "red"))
        quit()


def show_and_save_to_summary(string):
    print(string)
    append_to_deployment_summary(strip_ansi_from_string(string))


def append_to_deployment_summary(string):
    append_string_to_file(string, summary_filepath)
