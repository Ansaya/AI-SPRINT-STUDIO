global mc, oscar_cli, ssh, ssh_key, script, amllibrary_no_sfs, amllibrary_sfs


class Mc:
    def __init__(self, mc_dir):
        self.mc = mc_dir + "mc "
        self.config = mc_dir + "mc_config"

    def get_command(self, command):
        return self.mc + "--config-dir " + self.config + " " + command


class Oscarcli:
    def __init__(self, oscar_cli_dir):
        self.oscar = oscar_cli_dir + "oscar-cli "
        self.config = oscar_cli_dir + "config.yaml"

    def get_command(self, command):
        return self.oscar + command + " --config " + self.config


def init(work_dir):
    global mc, oscar_cli, ssh, ssh_key, script, amllibrary_no_sfs, amllibrary_sfs

    executables_dir = work_dir + ".executables/"
    mc = Mc(executables_dir)
    oscar_cli = Oscarcli(executables_dir)
    ssh = executables_dir + "ssh_private_key.json"
    ssh_key = executables_dir + "id_rsa"
    script = executables_dir + "script.sh"
    amllibrary_no_sfs = work_dir + "aMLLibrary-config-noSFS.ini"
    amllibrary_sfs = work_dir + "aMLLibrary-config-SFS.ini"
