import os
import yaml

class Application:
    @staticmethod
    def read(data):
        if isinstance(data, str):
            with open(data, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)