# this file calls all methods needed for the whole campaign
# tried to keep it as slim as possible for easier reading (failed miserably)

import os

import executables

from termcolor import colored

from cluster_manager import remove_all_buckets, generate_fdl_configuration, apply_cluster_configuration, \
    remove_all_services, apply_fdl_configuration_wrapped
from gui import show_runs
from input_file_processing import show_workflow, run_scheduler, get_run_info, \
    get_train_ml_models, get_clusters_info, get_simple_services, get_do_final_processing
from postprocessing import prepare_runtime_data, plot_runtime_core_graphs, make_runtime_core_csv, save_dataframes
from process_logs import make_csv_table, make_done_file
from retrieve_logs import pull_logs
from run_manager import move_input_files_to_input_bucket, wait_services_completion
from utils import auto_mkdir, show_warning, delete_directory

global run_dir, clusters, runs, run, simple_services, repetitions, run_name, current_deployment_dir


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


def final_processing():
    print(colored("\nFinal processing...", "blue"))
    results_dir = current_deployment_dir + "/results"
    auto_mkdir(results_dir)

    process_subfolder(results_dir, simple_services)

    if get_train_ml_models():
        from mllibrary_manager import run_mllibrary

        run_mllibrary(results_dir, run_name)
        # plot_ml_predictions_graphs(results_dir, run_name)

    make_done_file(results_dir)
    print(colored("Done!", "green"))
    # print("\n\n")
    return


def process_subfolder(results_dir, services):
    df, adf = prepare_runtime_data(run_dir, repetitions, runs, services)
    # make_statistics(campaign_dir, results_dir, subfolder, services)
    plot_runtime_core_graphs(results_dir, run_name, df, adf)
    make_runtime_core_csv(results_dir, run_name, df)

    # not needed, the full runtime_core is generated elsewhere
    """
    if get_train_ml_models():
        make_runtime_core_csv_for_ml(results_dir, df, adf, "Interpolation")
        make_runtime_core_csv_for_ml(results_dir, df, adf, "Extrapolation")
    """

    save_dataframes(results_dir, run_name, df, adf)


def manage_campaign_dir():
    """
    if the campaign_dir already exists, and a "Results" folder is present, it exits,
    otherwise it finds the last run (i.e. "Run #11"), it deletes it (it may have failed) and resumes from there
    if the run_dir doesn't exist it creates it and starts as normal
    :return: the index of the next run to execute; this is the index from the list "runs", not the run id (i.e. run
            with index 0 has id "Run #1")
    """

    if os.path.exists(current_deployment_dir) and os.path.isdir(current_deployment_dir):
        folder_list = os.listdir(current_deployment_dir)
        if "results" in folder_list:  # if there's a Result folder, the specific deployment has been completely tested
            if os.path.exists(current_deployment_dir + "/results/done"):
                show_warning("Run completed, skipping...")
                return -1
            else:
                delete_directory(current_deployment_dir + "/results")
                final_processing()
                return -1

        show_warning("Folder exists, resuming...")
        folder_list = os.listdir(run_dir)

        if folder_list:
            n = len(folder_list) - 1

            last_run = run_dir + "/" + runs[n]["id"]
            # print(last_run)
            if os.path.exists(last_run + "/done"):
                n += 1
            else:
                delete_directory(last_run)
        else:
            return 0

    else:
        n = 0
        os.mkdir(current_deployment_dir)
        os.mkdir(run_dir)

    os.system("cp input.yaml '" + current_deployment_dir + "/input.yaml'")

    return n


def main(clean_buckets=False):
    global clusters, runs, simple_services, run_name, current_deployment_dir, run_dir, repetitions
    clusters = get_clusters_info()
    base, runs = run_scheduler()
    simple_services = get_simple_services(runs[0]["services"])
    campaign_dir, run_name, repetitions, cooldown = get_run_info()

    # campaign_dir = work_dir + campaign_dir
    # auto_mkdir('/'.join(campaign_dir.split("/")[:-1]))  # sneaky cheaty but my brain hurts so I'm excused
    # auto_mkdir(campaign_dir)
    current_deployment_dir = campaign_dir + "/" + run_name
    run_dir = current_deployment_dir + "/runs"

    s = manage_campaign_dir()
    if s == -1:
        return

    show_workflow(simple_services)
    show_runs(base, repetitions, clusters, current_deployment_dir)

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

    if get_do_final_processing():
        final_processing()
    return


if __name__ == '__main__':
    main()
