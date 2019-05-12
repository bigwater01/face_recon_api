import logging
import os
import os.path as osp
import matlab.engine
import subprocess
from Fit3DMM.fit_3dmm import *

from name_rules import *


class NICPInvariants:
    def __init__(self, source_free_face, source_landmarks, target_free_faces):
        self.source_free_faces = source_free_face
        self.source_features = source_landmarks
        self.target_free_faces = target_free_faces
        self.is_valid = False

        self.check_valid()

    def check_valid(self):
        c0 = osp.isfile(self.source_free_faces)
        c1 = osp.isfile(self.source_features)
        c2 = osp.isfile(self.target_free_faces)
        self.is_valid = c0 and c1 and c2


class ReconElement:
    def __init__(self):
        self.base_name = ""
        self.root_path = ""
        # self.nicp_execute = ""
        # self.fd_execute = ""
        self.map_file = ""

        self.has_raw = False
        self.has_obj = False
        self.has_rgbd = False
        self.has_landmarks = False
        self.has_landmarks_2d = False
        self.has_landmarks_3d = False
        self.has_mfm_model = False

    def run_face_recon(self, face_recon_exe, map_file, config_file):
        self.check_status()
        if self.has_raw:
            subprocess.call([face_recon_exe, config_file, self.root_path, map_file], shell=False)
            self.has_obj = osp.isfile(osp.join(self.root_path, OBJ_folder, self.base_name + OBJ_suffix))
            self.has_rgbd = osp.isfile(osp.join(self.root_path, RGBD_folder, self.base_name + RGBD_FILE_suffix))
            self.has_landmarks = osp.isfile(osp.join(self.root_path, LANDMARKS_folder,
                                                     self.base_name + LANDMARKS_RAW_suffix))
        else:
            logging.warning("Invalid source for FaceRecon at path %s." % self.base_name)

    def generate_2d_and_3d_landmarks(self, matlab_engine):
        if not self.has_obj and self.has_landmarks:
            logging.warning("Fail to generate 2d and 3d landmarks due to insufficient of obj or landmark files "
                            "at path %s." % self.root_path)
        if not matlab_engine._check_matlab():
            logging.warning("Fail to generate 2d and 3d landmarks due to no matlab engine "
                            "at path %s." % self.root_path)
        obj_file = osp.join(self.root_path, OBJ_folder, self.base_name + OBJ_suffix)
        landmarks_file = osp.join(self.root_path, LANDMARKS_folder, self.base_name + LANDMARKS_RAW_suffix)
        try:
            matlab_engine.get_landmark_3d(obj_file, landmarks_file, nargout=0)
            self.has_landmarks_2d = osp.isfile(osp.join(self.root_path, LANDMARKS_folder,
                                                        self.base_name + LANDMARKS_2D_suffix))
            self.has_landmarks_3d = osp.isfile(osp.join(self.root_path, LANDMARKS_folder,
                                                        self.base_name + LANDMARKS_3D_suffix))
        except Exception as e:
            logging.error("Error while running generate_2d_and_3d_landmarks at path %s, "
                          "error type is %s" % (self.root_path, type(e).__name__))

    def generate_3dmm_models(self, matlab_engine):
        if not self.has_rgbd:
            logging.warning("Fail to generate 3dmm_model due to insufficient of rgbd file "
                            "at path %s." % self.root_path)
        if not matlab_engine._check_matlab():
            logging.warning("Fail to generate 2d and 3d landmarks due to no matlab engine "
                            "at path %s." % self.root_path)

        rgbd_file = osp.join(self.root_path, RGBD_folder, self.base_name + MONO_FILE_suffix)
        output_path = osp.join(self.root_path, OUTPUT_folder)
        if not osp.isdir(output_path):
            os.mkdir(output_path)
        bfm_params_file = osp.join(output_path, self.base_name + BFM_PARAMS_suffix)
        try:
            generate_3dmm_params(rgbd_file, output_path)
        except NoInputFileError:
            logging.warning("The input file for generating 3dmm params does not exist: %s." % rgbd_file)
            return
        except NoDetectorError:
            logging.warning("The input image for generating 3dmm params needs crop but no detector found: %s."
                            % rgbd_file)
            return
        except Exception as e:
            logging.warning("Exception %s was caught while running generate_3dmm_params at path %s."
                            % (type(e).__name__, self.root_path))
            return

        mfm_model_file = osp.join(output_path, self.base_name + MFM_MESH_suffix)
        try:
            matlab_engine.bfm2mfm_from_file(bfm_params_file, mfm_model_file, nargout=0)
            self.has_mfm_model = osp.isfile(osp.join(self.root_path, OUTPUT_folder, self.base_name + MFM_MESH_suffix))
        except Exception as e:
            logging.error("Error while running generate_3dmm_models at path %s, "
                          "error type is %s" % (self.root_path, type(e).__name__))

    def run_nicp(self, nicp_exe, option_file, invariants, calib_matrix, source_file=None):
        if not osp.isfile(nicp_exe) or not osp.isfile(option_file) or not osp.isfile(calib_matrix):
            logging.warning("Invalid NICP exe or config file or calib matrix file, path is: %s." % self.root_path)
            return
        if not invariants.is_valid():
            logging.warning("NICP invariants are invalid, path is: %s." % self.root_path)
            return

        if source_file is None:
            if self.has_mfm_model:
                source_file = osp.join(self.root_path, OUTPUT_folder, self.base_name + MFM_MESH_suffix)
            else:
                logging.warning("no source file for NICP, path is: %s." % self.root_path)
                return
        if not (self.has_landmarks_2d and self.has_landmarks_3d and self.has_obj):
            logging.warning("NICP variants are insufficient, path is: %s." % self.root_path)
            return

        command = [nicp_exe]
        command.extend(["--option", option_file])
        command.extend(["-s", source_file])
        command.extend(["--source-free-faces", invariants.source_free_faces])
        command.extend(["--source-features", invariants.source_features])
        command.extend(["-t", osp.join(self.root_path, OBJ_folder, self.base_name + OBJ_suffix)])
        command.extend(["--target-free-faces", invariants.target_free_faces])
        command.extend(["--target-features",
                        osp.join(self.root_path, LANDMARKS_folder, self.base_name + LANDMARKS_3D_suffix)])
        command.extend(["--target-features-2d",
                        osp.join(self.root_path, LANDMARKS_folder, self.base_name + LANDMARKS_2D_suffix)])
        command.extend(["--calib-matrix", calib_matrix])
        command.extend(["--output", osp.join(self.root_path, OUTPUT_folder)])
        command.extend(["--basename", self.base_name + NICP_MESH_suffix])

        logging.info("Recording nicp commands")
        logging.info(command)

        subprocess.call(command, shell=False)

    def check_status(self):
        color_path = osp.join(self.root_path, RAW_COLOR_folder)
        gray_path = osp.join(self.root_path, RAW_GRAY_folder)
        base_id = int(self.base_name)

        if base_id % 2 == 0:
            c0 = osp.isfile(osp.join(color_path, str(base_id) + RAW_COLOR_suffix))
            c1 = osp.isfile(osp.join(color_path, str(base_id + 1) + RAW_COLOR_suffix))
            g0 = osp.isfile(osp.join(gray_path, str(base_id * 3) + RAW_GRAY_suffix))
            g1 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 1) + RAW_GRAY_suffix))
            g2 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 2) + RAW_GRAY_suffix))
            g3 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 3) + RAW_GRAY_suffix))
            g4 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 4) + RAW_GRAY_suffix))
            g5 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 5) + RAW_GRAY_suffix))
        else:
            c0 = osp.isfile(osp.join(color_path, str(base_id - 1) + RAW_COLOR_suffix))
            c1 = osp.isfile(osp.join(color_path, str(base_id) + RAW_COLOR_suffix))
            g0 = osp.isfile(osp.join(gray_path, str(base_id * 3 - 3) + RAW_GRAY_suffix))
            g1 = osp.isfile(osp.join(gray_path, str(base_id * 3 - 2) + RAW_GRAY_suffix))
            g2 = osp.isfile(osp.join(gray_path, str(base_id * 3 - 1) + RAW_GRAY_suffix))
            g3 = osp.isfile(osp.join(gray_path, str(base_id * 3) + RAW_GRAY_suffix))
            g4 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 1) + RAW_GRAY_suffix))
            g5 = osp.isfile(osp.join(gray_path, str(base_id * 3 + 2) + RAW_GRAY_suffix))

        self.has_raw = c0 and c1 and g0 and g1 and g2 and g3 and g4 and g5

        self.has_obj = osp.isfile(osp.join(self.root_path, OBJ_folder, self.base_name + OBJ_suffix))
        self.has_rgbd = osp.isfile(osp.join(self.root_path, RGBD_folder, self.base_name + RGBD_FILE_suffix))
        self.has_landmarks = osp.isfile(osp.join(self.root_path, LANDMARKS_folder, self.base_name + RGBD_FILE_suffix))
        self.has_landmarks_2d = osp.isfile(osp.join(self.root_path, LANDMARKS_folder,
                                                    self.base_name + LANDMARKS_2D_suffix))
        self.has_landmarks_3d = osp.isfile(osp.join(self.root_path, LANDMARKS_folder,
                                                    self.base_name + LANDMARKS_3D_suffix))
        self.has_mfm_model = osp.isfile(osp.join(self.root_path, OUTPUT_folder, self.base_name + MFM_MESH_suffix))


def bilinear_smoothing(matlab_engine, param1, param2):
    pass