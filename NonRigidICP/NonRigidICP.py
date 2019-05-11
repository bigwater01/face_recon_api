from NonRigidICP.utils import *
import json
import matlab.engine

EXECUTE_FILE = r"C:\Users\bigwa\VSProjects\NonRigidICP\build\Release\NonRigidICP.exe"


class NICPElement:
    def __init__(self):
        self.source = ""
        self.source_free_faces = ""
        self.source_features = ""

        self.target = ""
        self.target_free_faces = ""
        self.target_features_3d = ""
        self.target_features_2d = ""
        self.calib_matrix = ""

        self.output_path = "."
        self.output_basename = "output"

        self.command = []

    def execute(self, exe_file, option_file):
        self.command.clear()
        self.command.append(exe_file)
        self.add_property("--option", option_file, forced=True)

        self.add_property("-s", self.source, forced=True)
        self.add_property("--source-free-faces", self.source_free_faces)
        self.add_property("--source-features", self.source_features)

        self.add_property("-t", self.target, forced=True)
        self.add_property("--target-free-faces", self.target_free_faces)
        self.add_property("--target-features", self.target_features_3d)
        self.add_property("--target-features-2d", self.target_features_2d)
        self.add_property("--calib-matrix", self.calib_matrix)

        self.add_property("--output", self.output_path, is_file=False)
        self.add_property("--basename", self.output_basename, is_file=False)

        print(self.command)
        subprocess.call(self.command, shell=False)

    def add_property(self, key, value, forced=False, is_file=True):
        if key.__len__() == 0 or value.__len__() == 0:
            if forced:
                self.warning()
            return
        if is_file and not osp.isfile(value):
            self.warning()
            return
        self.command.extend([key, value])

    def warning(self, msg=""):
        # raise error
        pass


class NonRigidICP:
    def __init__(self):
        # self.source_ext = ".ply"
        # self.target_ext = ".ply"

        self.option_files = []
        self.output_dir = ""
        self.output_basename = ""

        # lode modes:
        # ["single"]
        # ["folder", "sub_folder1", "sub_folder2", ..., "file_pattern"]
        self.load_mode = ["single"]
        self.source_path = ""
        self.source_free_faces_path = ""
        self.source_features_path = ""
        self.target_path = ""
        self.target_free_faces_path = ""
        self.target_features_2d_path = ""
        self.target_features_3d_path = ""
        self.calib_matrix = ""

        self.tasks = []

    def load_from_json_file(self, fn):

        with open(fn) as json_file:
            json_content = json.loads(json_file.read())

            try:
                # properties = json_content["properties"]
                # self.source_ext = properties.get("source-ext")
                # self.target_ext = properties.get("target-ext")

                options = json_content["options"]
                self.option_files = options["option-files"]
                self.output_dir = options["output-dir"]
                self.output_basename = options["output-basename"]

                data = json_content["data"]
                self.load_mode = data["load-mode"]

                self.source_path = data["source"]
                self.source_free_faces_path = data["source-free-faces"]
                self.source_features_path = data["source-features"]

                self.target_path = data["target"]
                self.target_free_faces_path = data["target-free-faces"]
                self.target_features_2d_path = data["target-features-2d"]
                self.target_features_3d_path = data["target-features-3d"]
                self.calib_matrix = data["calib-matrix"]

            except KeyError:
                self.warning()

    def save_to_json_file(self, fn):
        pass

    def warning(self, msg=""):
        # raise error
        pass

    def pretreatment(self):
        if self.load_mode[0] == "folder":
            target_files = list_all_files(self.target_path, ext=".ply")
            target_files_obj = list_all_files(self.target_path, ext=".obj")
            if target_files.__len__() == 0 and target_files_obj.__len__() > 0:
                [meshlab_obj2ply(f, osp.splitext(f)[0] + ".ply") for f in target_files_obj]
                target_files = list_all_files(self.target_path, ext=".ply")
            target_features_2d_files = list_all_files(self.target_features_2d_path)
            target_features_3d_files = list_all_files(self.target_features_3d_path)
        elif self.load_mode[0] == "single":
            target_files = [self.target_path] if osp.isfile(self.target_path) \
                                                 and osp.splitext(self.target_path)[1] == ".ply" else []
            target_features_2d_files = [self.target_features_2d_path] if osp.isfile(self.target_features_2d_path) else []
            target_features_3d_files = [self.target_features_3d_path] if osp.isfile(self.target_features_3d_path) else []
        else:
            self.warning()
            return

        if osp.isdir(self.source_path):
            source_files = list_all_files(self.source_path)
        else:
            source_files = [self.source_path] * target_files.__len__()

        if source_files.__len__() != target_files.__len__():
            self.warning()
            return

        target_free_faces = [self.target_free_faces_path] * target_files.__len__()
        use_3d_features = target_files.__len__() == target_features_3d_files.__len__()
        use_2d_features = target_files.__len__() == target_features_2d_files.__len__() and osp.isfile(self.calib_matrix)

        for i in range(source_files.__len__()):
            element = NICPElement()

            element.source = source_files[i]
            element.source_free_faces = self.source_free_faces_path
            element.source_features = self.source_features_path

            element.target = target_files[i]
            element.target_free_faces = target_free_faces[i]
            if use_3d_features:
                element.target_features_3d = target_features_3d_files[i]
            if use_2d_features:
                element.target_features_2d = target_features_2d_files[i]
                element.calib_matrix = self.calib_matrix

            element.output_path = self.output_dir
            element.output_basename = self.output_basename + "_" + str(i)

            self.tasks.append(element)

    def run(self):
        for i in range(self.option_files.__len__()):
            for element in self.tasks:
                # assert type(element) == NICPElement
                element.execute(EXECUTE_FILE, self.option_files[i])


def bilinear_smooth(root_path, input_filename, output_filename, num_basis):
    eng = matlab.engine.start_matlab()
    eng.addpath('../matlab_utils')
    print([root_path, input_filename, output_filename, num_basis])
    eng.testBilinear(root_path, input_filename, output_filename, num_basis, nargout=0)
    eng.quit()
