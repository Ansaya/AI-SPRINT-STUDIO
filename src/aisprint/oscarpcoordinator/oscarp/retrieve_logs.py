# oscar and kubectl logs are saved as txts and processed in dictionaries saved as pickle files

import pickle
import os
from tqdm import tqdm

import executables

from termcolor import colored
from datetime import datetime, timedelta

from input_file_processing import get_time_correction
from cluster_manager import set_default_oscar_cluster, get_active_cluster
from utils import configure_ssh_client, get_ssh_output, get_command_output_wrapped, show_debug_info

global run_name


# todo must comment more everywhere

def pull_logs(name, services, clusters):
    print(colored("Collecting logs...", "yellow"))
    global run_name
    run_name = name
    os.system("mkdir \"" + run_name + "/logs_kubectl\"")
    os.system("mkdir \"" + run_name + "/logs_oscar\"")

    for service in services:
        service_name = service["name"]
        cluster = get_active_cluster(service, clusters)
        # client = configure_ssh_client(cluster)  # todo temporarily disabled
        client = None
        timed_job_list = get_timed_jobs_list(service_name, client, cluster)
        save_timelist_to_file(timed_job_list, service_name)

    print(colored("Done!", "green"))


# for a given service, it saves as text file a copy of the logs from OSCAR and kubectl, and also returns a timelist
# todo explain better in comment
def get_timed_jobs_list(service, client, cluster):
    date_format = "%Y-%m-%d %H:%M:%S"

    # pod_list = get_kubernetes_pod_list(client)  # todo restore

    set_default_oscar_cluster(cluster)

    command = executables.oscar_cli.get_command("service logs list " + service)
    logs_list = get_command_output_wrapped(command)

    if logs_list:
        logs_list.pop(0)

    timed_job_list = {}

    for line in tqdm(logs_list):
        segments = line.split('\t')
        job_name = segments[0]
        job_status = segments[1]
        job_create = datetime.strptime(segments[2], date_format)
        job_start = datetime.strptime(segments[3], date_format)
        job_finish = datetime.strptime(segments[4].rstrip('\n'), date_format)

        if job_status != "Succeeded":
            print(colored("Uh oh, something went wrong somewhere.", "red"))

        pod_node = ""
        pod_creation = ""

        # todo restore

        """
        for pod in pod_list:
            if job_name in pod:
                pod_name = pod.split()[1]
                pod_creation, pod_node = get_kubectl_log(client, pod_name)
        """

        bash_script_start, bash_script_end = get_oscar_log(service, job_name)

        timed_job_list[job_name] = {"service": service,
                                    "cluster": cluster,
                                    "node": pod_node,
                                    "job_create": job_create,
                                    "pod_create": pod_creation,
                                    "job_start": job_start,
                                    "bash_script_start": bash_script_start,
                                    "bash_script_end": bash_script_start,
                                    "job_finish": job_finish
                                    }

    return timed_job_list


# retrieve the content of the log of a given job
def get_oscar_log(service_name, job_name):
    # command = oscar_cli + "service logs get " + service_name + " " + job_name
    command = executables.oscar_cli.get_command("service logs get " + service_name + " " + job_name)
    output = get_command_output_wrapped(command)

    # date_format_precise = "%d-%m-%Y %H:%M:%S.%f"
    date_format_precise = "%Y-%m-%d %H:%M:%S,%f"

    time_correction = get_time_correction()

    with open(run_name + "/logs_oscar/" + job_name + ".txt", "w") as file:
        for line in output:
            # nanoseconds after finding the script it is executed
            if "Script file found in '/oscar/config/script.sh'" in line:
                # bash_script_start = line.split(" ")[1].replace("\n", "")
                bash_script_start = line.split(" - ")[0]
                # print(bash_script_start)
                bash_script_start = datetime.strptime(bash_script_start, date_format_precise) \
                                    + timedelta(hours=time_correction)
            # this happens immediately after the bash script exits
            if "Searching for files to upload in folder" in line:
                bash_script_end = line.split(" - ")[0]
                bash_script_end = datetime.strptime(bash_script_end, date_format_precise) \
                                  + timedelta(hours=time_correction)
            file.write(line)

    return bash_script_start, bash_script_end


def get_kubernetes_pod_list(client):
    command = "sudo kubectl get pods -A"
    return get_ssh_output(client, command)


# downloads and save to file the log for the specified pod, returns pod creation time and node
# the pod creation time is the only time not gathered from OSCAR, so it's easier to apply the time correction here
def get_kubectl_log(client, pod_name):
    command = "sudo kubectl describe pods " + pod_name + " -n oscar-svc"
    output = get_ssh_output(client, command)
    with open(run_name + "/logs_kubectl/" + pod_name + ".txt", "w") as file:
        for line in output:
            file.write(line)

    create_time = ""
    node = ""

    time_correction = get_time_correction()
    show_debug_info("Time correction: " + str(time_correction))

    for line in output:
        if "Start Time:" in line:
            create_time = line.split(", ", 1)[1].split(" +")[0]
            create_time = datetime.strptime(create_time, "%d %b %Y %H:%M:%S") + timedelta(hours=time_correction)
        if "Node:" in line:
            node = line.split(" ")[-1].split("/")[0]

    return create_time, node


# dumps a timelist to file
def save_timelist_to_file(timed_job_list, service_name):
    with open(run_name + "/time_table_" + service_name + ".pkl", "wb") as file:
        pickle.dump(timed_job_list, file, pickle.HIGHEST_PROTOCOL)
    return
