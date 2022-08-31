# this file calls all methods needed for the whole campaign
# tried to keep it as slim as possible for easier reading (failed miserably)

import os

from termcolor import colored

from cluster_manager import remove_all_buckets, clean_all_logs, generate_fdl_configuration, apply_cluster_configuration, \
    generate_fdl_single_service, remove_all_services, create_bucket, apply_fdl_configuration_wrapped, \
    recreate_output_buckets
from gui import show_runs
from input_file_processing import show_workflow, run_scheduler, get_run_info, \
    get_service_by_name, get_use_ml_library, get_clusters_info, consistency_check, get_simple_services
from postprocessing import prepare_runtime_data, plot_runtime_core_graphs, make_runtime_core_csv, \
    make_runtime_core_csv_for_ml, plot_ml_predictions_graphs, save_dataframes, make_statistics
from process_logs import make_csv_table, make_done_file
from retrieve_logs import pull_logs
from run_manager import move_input_files_to_input_bucket, wait_services_completion
from utils import show_error, auto_mkdir, show_warning, delete_directory
from mllibrary_manager import run_mllibrary

global run_dir, clusters, runs, run, simple_services, repetitions, run_name


def prepare_clusters(clean_buckets):
    remove_all_services(clusters)
    if clean_buckets:
        remove_all_buckets(clusters)
    apply_cluster_configuration(run, clusters)
    generate_fdl_configuration(run["services"], clusters)
    apply_fdl_configuration_wrapped(run["services"])


def start_run_full():
    services = run["services"]
    move_input_files_to_input_bucket(services[0])
    wait_services_completion(services)


def end_run_full():
    working_dir = os.path.join(run_dir, run["id"])
    # os.mkdir(working_dir)
    pull_logs(working_dir, simple_services, clusters)
    make_csv_table(working_dir, run["services"], run["parallelism"], clusters)
    # download_bucket(campaign_dir + "/Database", "database")
    make_done_file(working_dir)


"""
def test_single_services():
    if not get_test_single_components():
        return

    remove_all_services(clusters)
    remove_all_buckets(clusters)

    is_first_service = True
    services = run["services"]
    for service in services:
        start_run_service(service, is_first_service)
        end_run_service(service)
        is_first_service = False


def start_run_service(service, is_first_service):
    print(colored("\nStarting " + run["id"] + " - " + service["name"], "blue"))
    # service = get_service_by_name(service_name, run["services"])

    # remove_all_services(clusters)
    generate_fdl_single_service(service, clusters)
    apply_fdl_configuration_wrapped([service])
    # recreate_output_buckets(service)

    if is_first_service:
        move_input_files_to_dead_start_bucket(service)
    else:
        move_bucket_to_dead_start_bucket(service)

    wait_services_completion([service])


def end_run_service(service):
    working_dir = os.path.join(campaign_dir, run["id"], service["name"])
    os.mkdir(working_dir)
    pull_logs(working_dir, [service], clusters)
    make_csv_table(working_dir, [service], run["parallelism"], clusters)
"""


def final_processing():
    print(colored("\nFinal processing...", "blue"))
    results_dir = run_dir + "/Results"
    auto_mkdir(results_dir)

    process_subfolder(results_dir, simple_services)

    """
    if get_test_single_components():
        for s in simple_services:
            process_subfolder(results_dir, s["name"], [s])
            # merge_csv_of_service(campaign_name, s["name"])
    print(colored("Done!", "green"))
    """

    run_mllibrary(results_dir, run_name)
    plot_ml_predictions_graphs(results_dir, run_name)

    make_done_file(results_dir)
    print(colored("Done!", "green"))
    print("\n\n")
    return


def process_subfolder(results_dir, services):
    df, adf = prepare_runtime_data(run_dir, repetitions, runs, services)
    # make_statistics(campaign_dir, results_dir, subfolder, services)
    plot_runtime_core_graphs(results_dir, run_name, df, adf)
    make_runtime_core_csv(results_dir, run_name, df)

    make_runtime_core_csv_for_ml(results_dir, df, adf, "Interpolation")
    # make_runtime_core_csv_for_ml(results_dir, df, adf, "Extrapolation")

    save_dataframes(results_dir, run_name, df, adf)


def manage_campaign_dir():
    """
    if the campaign_dir already exists, and a "Results" folder is present, it exits,
    otherwise it finds the last run (i.e. "Run #11"), it deletes it (it may have failed) and resumes from there
    if the run_dir doesn't exist it creates it and starts as normal
    :return: the index of the next run to execute; this is the index from the list "runs", not the run id (i.e. run
            with index 0 has id "Run #1")
    """

    if os.path.exists(run_dir) and os.path.isdir(run_dir):
        folder_list = os.listdir(run_dir)
        if "Results" in folder_list:  # if there's a Result folder, the specific run has been completed
            if os.path.exists(run_dir + "/Results/done"):
                show_warning("Run completed, skipping...")
                return -1
            else:
                delete_directory(run_dir + "/Results")
                final_processing()
                return -1

        show_warning("Folder exists, resuming...")
        folder_list.remove("input.yaml")
        folder_list.remove("campaign_summary.txt")

        n = len(folder_list) - 1

        last_run = run_dir + "/" + runs[n]["id"]
        # print(last_run)
        if os.path.exists(last_run + "/done"):
            n += 1
        else:
            delete_directory(last_run)

    else:
        n = 0
        os.mkdir(run_dir)
        os.system("cp input.yaml " + run_dir + "/input.yaml")

    return n


def main(clean_buckets=False):
    global clusters, runs, simple_services, run_name, run_dir, repetitions
    clusters = get_clusters_info()
    base, runs = run_scheduler()
    simple_services = get_simple_services(runs[0]["services"])
    campaign_dir, run_name, repetitions, cooldown = get_run_info()

    # print(clusters["vm_cluster"])
    # print(runs[0]["services"][0])

    auto_mkdir(campaign_dir)
    run_dir = campaign_dir + "/" + run_name

    s = manage_campaign_dir()
    if s == -1:
        return

    # consistency_check(simple_services)
    show_workflow(simple_services)
    show_runs(base, repetitions, clusters, run_dir)

    # run = runs[0]
    # test()

    for i in range(s, len(runs)):
        global run
        run = runs[i]
        print(colored("\nStarting " + run["id"] + " of " + str(len(runs)), "blue"))
        os.mkdir(os.path.join(run_dir, run["id"]))  # creates the working directory
        simple_services = get_simple_services(run["services"])

        prepare_clusters(clean_buckets)
        start_run_full()
        end_run_full()
        # test_single_services()

    # final_processing()  # todo condition must be added to input file
    return


if __name__ == '__main__':
    main()
