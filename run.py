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

def output_results_html(results, dest):

    # group by the test name
    grouped_results = {}

    for r in results:
        test_name = r['name']

        if test_name not in grouped_results:
            grouped_results[test_name] = []
        
        grouped_results[test_name].append(r)

    content = '<h1>Tests Run</h1>'

    content += '<ul>'

    for test_name in grouped_results.keys():
        content += '<li><a href="#%s">%s</a></li>' % (test_name, test_name)
        
    content += '</ul>'

    for test_name in grouped_results.keys():
        content += '<a name="%s"></a>' % test_name
        content += '<h1>%s</h1>' % test_name

        for r in grouped_results[test_name]:
            content += '''
                <div>
                    <h3>%s (%s)</h3>
                    <img src="../%s" />
                    <img src="../%s" />
                    <p>
                        <div><b>Command:</b> %s</div>
                        <div><b>Result:</b> %s</div>
                        <div><b>Execution time:</b> %ss</div>
                    </p>
                </div>
                <hr />
            ''' % (test_name, r['input'], r['input'], r['output'], r['cmd'], r['result'], r['time'])

    html = '''
        <html>
            <head><title>Results</title></head>
            <body>
                %s
            </body>
        </html>
    ''' % content

    with open(dest, 'w') as f:
        f.write(html)


def run_tests(file_path):
    num_tests = len(TESTS)
    results = []

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
        result = None

        while task.poll() is None and time_elapsed < TIMEOUT_SEC:
            time.sleep(delay)
            time_elapsed += delay

        if task.poll() is None:
            task.terminate()
            result = 'TIMEOUT'
        else:
            result = 'COMPLETED'

        results.append({
            "name": test_data["name"],
            "result": result,
            'input': file_path,
            "output": dest_path,
            'cmd': test_data["cmd"],
            "time": time_elapsed,
        })

    return results

#### MAIN #####################################

# Delete anything in the output dir
if os.path.isdir(OUTPUT_PATH):
    shutil.rmtree(OUTPUT_PATH)

os.mkdir(OUTPUT_PATH)

all_results = []

for path, subdirs, files in os.walk(MEDIA_PATH):
    for file_name in files:
        file_path = os.path.join(path, file_name)

        print("-- Running Tests for %s --" % (file_path))

        all_results += run_tests(file_path)

        print("")
        print("")

print("----------------------------------------")
print("")
print("")

tests_run = len(all_results)
failures =  [r for r in all_results if r['result'] == 'TIMEOUT']

print("-- Results: ran %d tests, %d failures --" % (tests_run, len(failures)))

if len(failures) > 0:
    for failure in failures:
        print(f)

# Write results file
output_results_html(results=all_results, dest="%s/_results.html" % OUTPUT_PATH)
