# Python imports: pathlib for pointing to the config file, tomllib to read the
# config file in TOML format
import pathlib
import tomllib

CONFIGURATION_FILE_NAME = "rankor_config.toml"
rankor_config = {}

config_path = pathlib.Path(__file__).parent / CONFIGURATION_FILE_NAME

with config_path.open(mode="rb") as configuration_file:
    rankor_config = tomllib.load(configuration_file)
