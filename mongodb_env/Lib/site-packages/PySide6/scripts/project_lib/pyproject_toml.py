# Copyright (C) 2025 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only
from __future__ import annotations

import sys
from pathlib import Path

import tomlkit
from tomlkit.toml_file import TOMLFile
from . import PYPROJECT_JSON_PATTERN
from .pyproject_parse_result import PyProjectParseResult
from .pyproject_json import parse_pyproject_json


def parse_pyproject_toml(pyproject_toml_file: Path) -> PyProjectParseResult:
    """
    Parse a pyproject.toml file and return a PyProjectParseResult object.
    """
    result = PyProjectParseResult()
    try:
        root_table = TOMLFile(pyproject_toml_file).read()
    except Exception as e:
        result.errors.append(str(e))
        return result

    tool_table = root_table.get("tool")
    if not tool_table:
        result.errors.append("Missing [tool] table")
        return result

    pyside_table = tool_table.get("pyside6-project")
    if not pyside_table:
        result.errors.append("Missing [tool.pyside6-project] table")
        return result

    files = pyside_table.get("files")
    if not isinstance(files, list):
        result.errors.append("Missing or invalid files list")
        return result

    for file in files:
        if not isinstance(file, str):
            result.errors.append(f"Invalid file: {file}")
            return result

        file_path = Path(file)
        if not file_path.is_absolute():
            file_path = (pyproject_toml_file.parent / file).resolve()

        result.files.append(file_path)

    return result


def write_pyproject_toml(pyproject_file: Path, project_name: str, project_files: list[str]):
    """
    Create or update a pyproject.toml file with the specified content.

    Raises a ValueError if the project file is not a valid TOML file.

    :param pyproject_file: The pyproject.toml file path to create or update.
    :param project_name: The name of the project.
    :param project_files: The relative paths of the files to include in the project.
    """
    if pyproject_file.exists():
        try:
            doc = TOMLFile(pyproject_file).read()
        except Exception as e:
            raise f"Error parsing TOML: {str(e)}"
    else:
        doc = tomlkit.document()

    project_table = doc.setdefault("project", tomlkit.table())
    project_table["name"] = project_name

    tool_table = doc.setdefault("tool", tomlkit.table())
    pyside_table = tool_table.setdefault("pyside6-project", tomlkit.table())

    pyside_table["files"] = sorted(project_files)

    pyproject_file.write_text(tomlkit.dumps(doc), encoding="utf-8")


def migrate_pyproject(pyproject_file: Path | str = None) -> int:
    """
    Migrate a project *.pyproject JSON file to the new pyproject.toml format.

    The containing subprojects are migrated recursively.

    :return: 0 if successful, 1 if an error occurred.
    """
    project_name = None

    # Transform the user input string into a Path object
    if isinstance(pyproject_file, str):
        pyproject_file = Path(pyproject_file)

    if pyproject_file:
        if not pyproject_file.match(PYPROJECT_JSON_PATTERN):
            print(f"Cannot migrate non \"{PYPROJECT_JSON_PATTERN}\" file:", file=sys.stderr)
            print(f"\"{pyproject_file}\"", file=sys.stderr)
            return 1
        project_files = [pyproject_file]
        project_name = pyproject_file.stem
    else:
        # Get the existing *.pyproject files in the current directory
        project_files = list(Path().glob(PYPROJECT_JSON_PATTERN))
        if not project_files:
            print(f"No project file found in the current directory: {Path()}", file=sys.stderr)
            return 1
        if len(project_files) > 1:
            print("Multiple pyproject files found in the project folder:")
            print('\n'.join(str(project_file) for project_file in project_files))
            response = input("Continue? y/n: ")
            if response.lower().strip() not in {"yes", "y"}:
                return 0
        else:
            # If there is only one *.pyproject file in the current directory,
            # use its file name as the project name
            project_name = project_files[0].stem

    # The project files that will be written to the pyproject.toml file
    output_files = set()
    for project_file in project_files:
        project_data = parse_pyproject_json(project_file)
        if project_data.errors:
            print(f"Invalid project file: {project_file}. Errors found:", file=sys.stderr)
            print('\n'.join(project_data.errors), file=sys.stderr)
            return 1
        output_files.update(project_data.files)

    project_folder = project_files[0].parent.resolve()
    if project_name is None:
        # If a project name has not resolved, use the name of the parent folder
        project_name = project_folder.name

    pyproject_toml_file = project_folder / "pyproject.toml"
    if pyproject_toml_file.exists():
        already_existing_file = True
        try:
            doc = TOMLFile(pyproject_toml_file).read()
        except Exception as e:
            raise f"Error parsing TOML: {str(e)}"
    else:
        already_existing_file = False
        doc = tomlkit.document()

    project_table = doc.setdefault("project", tomlkit.table())
    if "name" not in project_table:
        project_table["name"] = project_name

    tool_table = doc.setdefault("tool", tomlkit.table())
    pyside_table = tool_table.setdefault("pyside6-project", tomlkit.table())

    pyside_table["files"] = sorted(
        p.relative_to(project_folder).as_posix() for p in output_files
    )

    toml_content = tomlkit.dumps(doc).replace('\r\n', '\n').replace('\r', '\n')

    if already_existing_file:
        print(f"WARNING: A pyproject.toml file already exists at \"{pyproject_toml_file}\"")
        print("The file will be updated with the following content:")
        print(toml_content)
        response = input("Proceed? [Y/n] ")
        if response.lower().strip() not in {"yes", "y"}:
            return 0

    try:
        Path(pyproject_toml_file).write_text(toml_content)
    except Exception as e:
        print(f"Error writing to \"{pyproject_toml_file}\": {str(e)}", file=sys.stderr)
        return 1

    if not already_existing_file:
        print(f"Created \"{pyproject_toml_file}\"")
    else:
        print(f"Updated \"{pyproject_toml_file}\"")

    # Recursively migrate the subprojects
    for sub_project_file in filter(lambda f: f.match(PYPROJECT_JSON_PATTERN), output_files):
        result = migrate_pyproject(sub_project_file)
        if result != 0:
            return result
    return 0
