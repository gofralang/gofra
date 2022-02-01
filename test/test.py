# Gofra test source.
# Tests all the examples/source/test.

# Importing.
import subprocess
import shlex
import typing
import time
import os
import sys


def cli_execute(commands: typing.List[str]) -> subprocess.CompletedProcess:
    """ Executes CLI command. """
    return subprocess.run(" ".join(map(shlex.quote, commands)), capture_output=True)


# When we start tests.
test_start_time = time.time()

# Path to the language core.
LANG_PATH = "../src/gofra.py"

# Should we run MyPy?
MYPY_RUN = True

# If we should record new, and not test.
RECORD_NEW = False

# If true, stop processing if there is failure at one of the tests.
STOP_AT_FAILURE = False

# Run Python/Dump/Graph.
RUN_OTHER = True

# Should we clear after?
CLEAR_AFTER = True

# Test records dir.
TEST_RECORDS_DIRECTORY = "./records/"

# Test extension.
TEST_EXTENSION = ".gof"

# Directories to run test on.
TEST_DIRECTORIS = [
    ("../examples/", "/examples/"),
    ("../tests/", "/tests/")
]

for test_directory in TEST_DIRECTORIS:
    # Iterate over test directories.
    for test_file in os.listdir(test_directory[0]):
        # Iterate over test files.

        # Continue if not test extension.
        if os.path.splitext(test_file)[1] != TEST_EXTENSION:
            continue

        # Base command for CLI.
        cli_execute_path = test_directory[0] + test_file
        cli_base_command = ["python", LANG_PATH, cli_execute_path]

        # Run commands.
        run_result = cli_execute(cli_base_command + ["run", "-silent"])
        if RUN_OTHER:

            graph_result = cli_execute(cli_base_command + ["graph", "-silent"])
            python_result = cli_execute(cli_base_command + ["python", "-silent"])
            dump_result = cli_execute(cli_base_command + ["dump", "-silent"])
            for result in (graph_result, python_result, dump_result):
                if result.returncode != 0:
                    # Print.
                    print(f"[Test][Failed][OTHER] File {cli_execute_path} returned error code {run_result.returncode}, "
                          f"with error output: {run_result.stderr.decode('utf-8')}!", file=sys.stderr)

                    # Exit.
                    if STOP_AT_FAILURE:
                        exit(1)
        # Get run result.
        run_result_current = run_result.stdout.decode("utf-8")
        run_result_current = run_result_current.encode("unicode_escape").decode("utf-8")

        # Get record path.
        record_file_path = TEST_RECORDS_DIRECTORY + test_directory[1] + os.path.basename(cli_execute_path) + ".txt"

        if RECORD_NEW:
            # If we record.

            # Write result.
            with open(record_file_path, "w") as rf:
                rf.write(run_result_current)

        try:
            with open(record_file_path, "r") as record_file:
                # Read expected result.

                if run_result.returncode != 0:
                    # Print.
                    print(f"[Test][Failed] File {cli_execute_path} returned error code {run_result.returncode}, "
                          f"with error output: {run_result.stderr.decode('utf-8')}!", file=sys.stderr)

                    # Exit.
                    if STOP_AT_FAILURE:
                        exit(1)

                run_result_expected = "".join(record_file.readlines())

                if run_result_current != run_result_expected:
                    # If no same result.

                    # Print.
                    print(f"[Test][Failed] File {cli_execute_path} expected result \"{run_result_expected}\", "
                          f"but got \"{run_result_current}\"!", file=sys.stderr)

                    # Exit.
                    if STOP_AT_FAILURE:
                        exit(1)
                else:
                    # Print.
                    print(f"[Test][OK] File {cli_execute_path}!")

            # Clean after.
            if CLEAR_AFTER and RUN_OTHER:
                try:
                    os.remove(cli_execute_path + ".dot")
                    os.remove(cli_execute_path + ".py")
                except FileNotFoundError:
                    pass
        except FileNotFoundError:
            print(f"[Test][OK] File {cli_execute_path} does not have record file! Please run with RECORD_NEW!", file=sys.stderr)

# Run MyPy on the core.
if MYPY_RUN:
    try:
        mypy_results = cli_execute(["mypy", LANG_PATH])
    except FileNotFoundError:
        print(f"[MyPy][Failed]: MYPY is not installed!", file=sys.stderr)
    else:
        mypy_results = str(mypy_results.stdout.decode("utf-8"))
        if not mypy_results.startswith("Success"):
            print(f"[MyPy][Failed]:\n {mypy_results}", file=sys.stderr)
            # Exit.
            if STOP_AT_FAILURE:
                exit(1)
        else:
            print(f"[MyPy][OK]!")
        if CLEAR_AFTER:
            try:
                os.remove(".mypy_cache")
            except PermissionError:
                pass
else:
    print(f"[MyPy][Disabled]!")

# Messages.
if RECORD_NEW:
    print("[Test][Records] Test records new recorded OK!")
if CLEAR_AFTER:
    print("[Test][Junk][Cleared]!")

# Print time taken.
test_time_taken = int(time.time() - test_start_time)
print(f"[Test] End! Time taken: {test_time_taken}s")
