global mc, oscar_cli, ssh, ssh_key


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


def init(executables_dir):
    global mc, oscar_cli, ssh, ssh_key

    mc = Mc(executables_dir)
    oscar_cli = Oscarcli(executables_dir)
    ssh = executables_dir + "ssh_private_key.json"
    ssh_key = executables_dir + "id_rsa"
