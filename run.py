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

    for i, test_data in enumerate(TESTS):
        sys.stdout.write("%d of %d (%s): " % (i+1, num_tests, test_data["name"]))

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
            sys.stdout.write("FAILED (timed out)\n")
        else:
            sys.stdout.write("SUCCESS\n")


#### MAIN #####################################

# Delete anything in the output dir
if os.path.isdir(OUTPUT_PATH):
    shutil.rmtree(OUTPUT_PATH)

os.mkdir(OUTPUT_PATH)

files = os.listdir(MEDIA_PATH)

for file_name in files:
    file_path = MEDIA_PATH + file_name

    print("-- Running Tests for %s --" % (file_path))
    
    run_tests(file_path)

    print("")
    print("")

