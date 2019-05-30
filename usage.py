from NonRigidICP.NonRigidICP import NonRigidICP
from NonRigidICP.utils import meshlab_run_script
from Fit3DMM.fit_3dmm import generate_3dmm_params
from ReconElement import NICPInvariants, ReconElement, bilinear_smoothing
import os.path as osp
import os
import shutil
from name_rules import *
import matlab.engine
import logging

MAP_MAP = {range(1, 92): r"F:\bmap\b_map1.dat",
           range(92, 116): r"F:\bmap\b_map2.dat",
           range(116, 166): r"F:\bmap\b_map3.dat",
           range(166, 291): r"F:\bmap\b_map4.dat",
           range(291, 391): r"F:\bmap\b_map5.dat",
           range(391, 410): r"F:\bmap\b_map6.dat",
           range(410, 430): r"F:\bmap\b_map7.dat",
           range(430, 434): r"F:\bmap\b_map8.dat",
           range(434, 548): r"F:\bmap\b_map9.dat",
           range(548, 999): r"F:\bmap\b_map10.dat"}


def get_map_file(human_id):
    for id_range, map_path in MAP_MAP.items():
        if human_id in id_range:
            return map_path


if __name__ == "__main__":
    logging.basicConfig(filename='tmp.log', level=logging.INFO)

    ff_source = r"F:\NICP_utils\source\ff_mfm_model_smaller_face"
    source_features = r"F:\NICP_utils\source\mfm_model_features.txt"
    ff_target = r"F:\NICP_utils\target\ff_target"
    inv = NICPInvariants(ff_source, source_features, ff_target)
    if not inv.is_valid:
        print("Invalid invaris")
        # sys.exit(-1)

    matlab_engine = matlab.engine.start_matlab()
    matlab_engine.addpath(r"C:\Users\bigwa\MatlabProjects\3dlandmarks\lm")
    matlab_engine.addpath(r"C:\Users\bigwa\MatlabProjects\bfm2mfm")

    recon_exe = r"F:\FaceDetector_QT\FaceDetector_QT.exe"
    recon_config = r"F:\FaceDetector_QT\fd_config.txt"

    rm_iso_pieces_script = r"F:\NICP_utils\rm_iso_pieces.mlx"

    root_path = r"F:\selectedConvertedScanData"
    all_humans = [f for f in os.listdir(root_path) if osp.isdir(osp.join(root_path, f))]
    for human in all_humans:
        human_folder = osp.join(root_path, human)
        all_motions = [f for f in os.listdir(human_folder) if osp.isdir(osp.join(human_folder, f))]
        for motion in all_motions:
            if motion != "1":
                continue
            current_path = osp.join(root_path, human, motion)
            for base_name in [osp.splitext(fn)[0] for fn in os.listdir(osp.join(current_path, RAW_COLOR_folder))]:
                recon = ReconElement()
                recon.root_path = current_path
                recon.base_name = base_name

                if base_name == "0000":
                    recon.check_status()
                    # map_file = get_map_file(int(human.strip('B')))
                    # recon.run_face_recon(recon_exe, map_file, recon_config)
                    #
                    # obj_file = osp.join(recon.root_path, OBJ_folder, recon.base_name + OBJ_suffix)
                    # meshlab_run_script(obj_file, obj_file, rm_iso_pieces_script)
                    #
                    # recon.generate_2d_and_3d_landmarks(matlab_engine)
                    #
                    # recon.generate_3dmm_models(matlab_engine)

                    nicp_exe = r"C:\Users\bigwa\VSProjects\NonRigidICP_CWen\build\Release\NonRigidICP.exe"
                    nicp_options = r"F:\NICP_utils\options_CWen.txt"
                    calib_matrix = r"F:\NICP_utils\target\calib_matrix.txt"
                    mfm_model = r"D:/result_new/" + human + "-1-0000-mfm.obj"
                    mfm_model_ply = osp.join(recon.root_path, OUTPUT_folder, recon.base_name + "_mfm2.ply")
                    meshlab_run_script(mfm_model, mfm_model_ply, rm_iso_pieces_script)

                    if int(human.strip("B")) > 420:
                        recon.generate_2d_and_3d_landmarks(matlab_engine)

                    recon.run_nicp(nicp_exe, nicp_options, inv, calib_matrix, source_file=mfm_model_ply)
                    output_file = osp.join(recon.root_path, OUTPUT_folder, recon.base_name + NICP_MESH_suffix)
                    out_file_copy_to = "D:/result_new/" + human + "-1-0000-nicp.ply"
                    shutil.copyfile(output_file, out_file_copy_to)
                    print("Job finished at path: %s." % current_path)
                    logging.info("Job finished at path: %s." % current_path)

    matlab_engine.quit()

