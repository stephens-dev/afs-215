from pathlib import Path

import yaml


class FileWriter:
    @staticmethod
    def write_to_file_in_sub_path(root_dir: Path, file_sub_path: Path, file_content: str):
        def create_dir_hierarchy_if_does_not_exist():
            file_full_path.parent.mkdir(parents=True, exist_ok=True)

        def write_to_file():
            with file_full_path.open('w') as file:
                file.write(file_content)

        file_full_path = root_dir / file_sub_path
        create_dir_hierarchy_if_does_not_exist()
        write_to_file()

    @staticmethod
    def write_yaml_to_file(file_path: Path, yaml_data: dict):
        with file_path.open('w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False)


class FileReader:
    @staticmethod
    def read_yaml(file_path: Path) -> dict:
        with file_path.open('r') as f:
            return yaml.load(f)
