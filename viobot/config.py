import yaml


def read(config_file):
    with open(config_file) as f:
        return yaml.safe_load(f.read())
