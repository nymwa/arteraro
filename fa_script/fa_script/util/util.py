from pathlib import Path
import yaml

def load_config(path = None):
    if path is None:
        path = 'config.yaml'
    with open(path) as f:
        config = yaml.safe_load(f)
    return config

def check_sub_config(path = None):
    if path is None:
        path = 'sub_config.yaml'
    return Path(path).exists()

def load_sub_config(path = None):
    if path is None:
        path = 'sub_config.yaml'
    with open(path) as f:
        config = yaml.safe_load(f)
    return config

def load_eval_config(config):
    eval_config_path = config['eval_config']
    with open(eval_config_path) as f:
        config = yaml.safe_load(f)
    return config