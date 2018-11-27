import os
from argparse import ArgumentParser
import subprocess
import shutil
import sys
import time

#### CLI ARGS #################################

parser = ArgumentParser()
parser.add_argument("-f", "--ffmpeg", dest="ffmpeg", default=None, help="Path to ffmpeg")
parser.add_argument("-v", "--verbose", dest="verbose", default=False, action="store_true", help="Verbose logs")
args = parser.parse_args()

#### CONSTANTS #################################

MEDIA_PATH = "./media/"
OUTPUT_PATH = "./output"
DEV_NULL = open(os.devnull, 'wb')
TIMEOUT_SEC = 10

TESTS = [
    {
        "name": "resize",
        "cmd": "-filter:v scale=iw/2:-2"
    },
    {
        "name": "crop",
        "cmd": "-filter:v crop=iw/2:ih/2:iw/4:ih/4"
    },
    {
        "name": "crop_optimize",
        "cmd": "-filter_complex '[0:v] scale=-1:200[s];[s] split [gen][use];[gen] palettegen=stats_mode=full [palette];[use][palette] paletteuse'"
    }
]

#### HELPERS ###################################

def run_tests(file_path):
    num_tests = len(TESTS)

    failures = []

    for i, test_data in enumerate(TESTS):
        output_string = "%d of %d (%s): " % (i+1, num_tests, test_data["name"])

        ffmpeg_path = args.ffmpeg if args.ffmpeg else "ffmpeg"
        base_name = os.path.basename(file_path)
        file_name, ext = os.path.splitext(base_name)
        dest_path = "%s/%s_%s%s" % (OUTPUT_PATH, file_name, test_data["name"], ext)
        full_cmd = "%s -loglevel debug -i %s %s -y %s" % (ffmpeg_path, file_path, test_data["cmd"], dest_path)

        task = None

        if args.verbose:
            task = subprocess.Popen(full_cmd, shell=True)
        else:
            task = subprocess.Popen(full_cmd, shell=True, stderr=DEV_NULL, stdout=DEV_NULL)

        delay = .01
        time_elapsed = 0

        while task.poll() is None and time_elapsed < TIMEOUT_SEC:
            time.sleep(delay)
            time_elapsed += delay

        if task.poll() is None:
            task.terminate()
            output_string += "FAILED (timed out)"
            failures.append(output_string)
        else:
            output_string += "SUCCESS"

        print(output_string)
    return failures


#### MAIN #####################################

# Delete anything in the output dir
if os.path.isdir(OUTPUT_PATH):
    shutil.rmtree(OUTPUT_PATH)

os.mkdir(OUTPUT_PATH)

total_failures = []

tests_run = 0

for path, subdirs, files in os.walk(MEDIA_PATH):
    for file_name in files:
        file_path = os.path.join(path, file_name)

        print("-- Running Tests for %s --" % (file_path))

        total_failures += run_tests(file_path)
        tests_run += len(TESTS)

        print("")
        print("")

print("----------------------------------------")
print("")
print("")

print("-- Results: ran %d tests, %d failures --" % (tests_run, len(total_failures)))

if len(total_failures) > 0:
    for failure in total_failures:
        print(failure)
