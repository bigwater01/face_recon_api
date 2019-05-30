import os.path as osp
import os
import subprocess

MESHLAB_SERVER_CMD = r"C:\Program Files\VCG\MeshLab\meshlabserver.exe"


def list_all_files(path, use_abs_path=True, contains="", ext=""):
    if not osp.isdir(path):
        return []

    if use_abs_path:
        all_files = [osp.join(path, f) for f in os.listdir(path) if osp.isfile(osp.join(path, f))]
    else:
        all_files = [f for f in os.listdir(path) if osp.isfile(osp.join(path, f))]

    if ext.__len__() > 0:
        all_files = [f for f in all_files if osp.splitext(f)[1] == ext]
    if contains.__len__() > 0:
        all_files = [f for f in all_files if f.find(contains) != -1]

    return all_files


def meshlab_obj2ply(input_path, output_path):
    subprocess.call([MESHLAB_SERVER_CMD, "-i", input_path, "-o", output_path, "-m", "vc", "vn", "vt", "fc", "wt"])


def meshlab_run_script(input_path, output_path, script_file):
    command = [MESHLAB_SERVER_CMD,
               "-i", input_path,
               "-o", output_path,
               "-m", "vc", "vn", "vt", "fc", "wt",
               "-s", script_file]
    subprocess.call(command, shell=False)
