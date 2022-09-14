import yaml


def make_oscar_p_input_file(deployment, testing_components, resources, run_parameters, images, is_single_service, service_number):
    # print(deployment, is_single_service)
    # print(testing_components)

    services = []
    clusters = []
    clusters_dict = {}

    i = service_number

    if is_single_service:
        run_parameters["input_files"]["storage_bucket"] = "bucket" + str(i)
        run_parameters["input_files"]["filename"] = None
    else:
        run_parameters["run"]["repetitions"] = 1
        run_parameters["run"]["final_processing"] = False

    for d in deployment:
        name = testing_components[d]["name"]
        r = d.split("@")[1]

        if is_single_service:
            input_bucket = "temp" + str(i)
            output_bucket = "trash" + str(i)
        else:
            input_bucket = "bucket" + str(i)
            output_bucket = "bucket" + str(i + 1)

        services.append({name: {
            "cluster": r,
            "image": images[d],
            "input_bucket": input_bucket,
            "output_bucket": output_bucket
        }})

        # easier to use a dict here to avoid duplications
        if r not in clusters_dict.keys():
            clusters_dict[r] = resources[r]

        i += 1

    # converts the dict to a list
    for c in clusters_dict.keys():
        clusters.append({c: clusters_dict[c]})

    oscar_p_input_file = {
        "services": services,
        "clusters": clusters,
    }

    # oscar_p_input_file = oscar_p_input_file | run_parameters
    oscar_p_input_file.update(run_parameters)

    oscar_p_input_file = {"configuration": oscar_p_input_file}

    with open("input.yaml", "w") as file:
        yaml.dump(oscar_p_input_file, file, sort_keys=False)

    # input(">_")


# todo temp function
"""
def get_image(d):
    images = {
        "C1@VM1": "scrapjack/blurry-faces-modded:stable",
        "C1@RasPi": "ghcr.io/srisco/blurry-faces-arm64",
        "C2@VM1": "scrapjack/mask-detector-modded:stable"
    }
    return images[d]

def get_image(d):
    images = {
        "C1@VM": "linuxserver/ffmpeg:amd64-version-4.4-cli",
        "C1@RasPi": "linuxserver/ffmpeg:arm64v8-4.4-cli-ls52",
        "C2@VM": "scrapjack/librosa:stable",
        "C3@VM": "linuxserver/ffmpeg:amd64-version-4.4-cli",
        "C3@RasPi": "linuxserver/ffmpeg:arm64v8-4.4-cli-ls52",
        "C4@VM": "linuxserver/ffmpeg:amd64-version-4.4-cli",
        "C5@AWS": "scrapjack/deepspeech:stable",
        "C5@VM": "scrapjack/deepspeech:stable",
        "C6@AWS": "ubuntu:20.04",
        "C6@VM": "ubuntu:20.04",
    }
    return images[d]
"""
