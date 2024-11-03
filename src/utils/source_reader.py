import json


def read_source_file(file_path="config/source.json"):
    with open(file_path, "r") as file:
        return json.load(file)
