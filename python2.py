import json
import argparse
import logging
import csv
import os
import shutil

class The_command:
    def execute(self, args):
        return "def!"


class Move_Last(The_command):
    def execute(self, args):
        src_dir, dest_dir = args
        files = os.listdir(src_dir)
        if not files:
            return f"we dont find No files {src_dir} to move."

        files.sort(key=lambda f: os.path.getctime(os.path.join(src_dir, f)))
        latest_file = files[-1]
        shutil.move(os.path.join(src_dir, latest_file), dest_dir)
        return f"we move the latest file, {latest_file}, from {src_dir} to {dest_dir}"


class Count(The_command):
    def execute(self, args):
        dir_p = args[0]
        return f"There are {len(os.listdir(dir_p))} file in the {dir_p}"


class Delete_File(The_command):
    def execute(self, args):
        file_p, dir_p = args
        file_to_delete = os.path.join(dir_p, file_p)
        if os.path.isfile(file_to_delete):
            os.remove(file_to_delete)
            return f"we delete the file {file_p} from {dir_p}"



class Rename_File(The_command):
    def execute(self, args):
        old_name, new_name, dir_p = args
        old_file = os.path.join(dir_p, old_name)
        new_file = os.path.join(dir_p, new_name)

        if os.path.isfile(old_file):
            os.rename(old_file, new_file)
            return f"we make Rename {old_name} to {new_name} in {dir_p}"
        else:
            return f"we dont find the file {old_name} in {dir_p} so the Rename failed."


class List_file(The_command):
    def execute(self, args):
        dir_p = args[0]
        return f" the file we found here {dir_p}: {os.listdir(dir_p)}"


class Sort_file(The_command):
    def execute(self, args):
        dir_p, criteria = args
        if criteria not in ["name", "date", "size"]:
            return f"you write wrong criteria: {criteria}. the correct criteria is one of : 'name', 'date', 'size'."

        files = os.listdir(dir_p)

        if criteria == "name":
            sorted_files = sorted(files)
        elif criteria == "date":
            sorted_files = sorted(files, key=lambda f: os.path.getctime(os.path.join(dir_p, f)))
        elif criteria == "size":
            sorted_files = sorted(files, key=lambda f: os.path.getsize(os.path.join(dir_p, f)))

        return f"the sorted from {dir_p} by {criteria} here : {sorted_files}"

class CategorizeCommand(The_command):
    def __init__(self, config):
        self.config = config

    def execute(self, args):
        dir_p = args[0]
        threshold_size_str = self.config.get("Threshold_size", "10KB")
        try:
            threshold_size = int(threshold_size_str.replace("KB", ""))
        except ValueError:
            return "wrong in threshold size in config."

        small_dir = os.path.join(dir_p, "smaller_than")
        large_dir = os.path.join(dir_p, "larger_than")
        os.makedirs(small_dir, exist_ok=True)
        os.makedirs(large_dir, exist_ok=True)

        for file in os.listdir(dir_p):
            file_path = os.path.join(dir_p, file)
            if os.path.isfile(file_path) and file_path not in [small_dir, large_dir]:
                file_size = os.path.getsize(file_path)
                if file_size < threshold_size * 1024:  # threshold_size is in KB
                    shutil.move(file_path, small_dir)
                else:
                    shutil.move(file_path, large_dir)

        return f"Categorized files in {dir_p} by size."

class CommandFactory:
    def __init__(self, config):
        self.config = config

    def create_command(self, command_name):
        if command_name == "mv_last":
            return Move_Last()
        elif command_name == "count":
            return Count()
        elif command_name == "delete":
            return Delete_File()
        elif command_name == "rename":
            return Rename_File()
        elif command_name == "list":
            return List_file()
        elif command_name == "sort":
            return Sort_file()
        elif command_name == "categorize":
            return CategorizeCommand(self.config)
        else:
            return The_command()


class ScriptExecutor:
    def __init__(self, command_factory):
        self.command_factory = command_factory

    def execute_script(self, script):
        commands = [line.strip() for line in script.split("\n") if line.strip()]
        results = []
        for command in commands:
            command_name, *args = command.split()
            command_instance = self.command_factory.create_command(command_name)
            try:
                result = getattr(command_instance, "execute")(args)
                results.append({"command": command_name, "result": result, "status": "passed"})
            except Exception as e:
                error_message = f"Error executing {command_name}: {str(e)}"
                results.append({"command": command_name, "result": error_message, "status": "failed"})
        return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Path to the input script file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output log file")
    args = parser.parse_args()

    with open("config.json") as f:
        config = json.load(f)

    logging.basicConfig(filename=args.output, level=logging.DEBUG)

    with open(args.input) as f:
        script = f.read()

    command_factory = CommandFactory(config)
    script_executor = ScriptExecutor(command_factory)

    results = script_executor.execute_script(script)

    if config["Output"] == "csv":
        with open(args.output, "w", newline="") as csvfile:
            fieldnames = ["command", "result", "status"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for command_result in results:
                writer.writerow(command_result)
    # log
    else:
        with open(args.output, "w") as logfile:
            for command_result in results:
                logfile.write(f"{command_result['command']}: {command_result['result']} [{command_result['status']}]\n")

if __name__ == "__main__":
    main()
