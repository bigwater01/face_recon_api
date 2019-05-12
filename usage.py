from NonRigidICP.NonRigidICP import NonRigidICP
from Fit3DMM.fit_3dmm import generate_3dmm_params
from ReconElement import NICPInvariants, ReconElement, bilinear_smoothing
import os.path as osp
import os
import sys
from name_rules import *

if __name__ == "__main__":
    # mission = NonRigidICP()
    # mission.load_from_json_file(".\\test.json")
    # mission.pretreatment()
    # mission.run()
    # print(1)

    ff_source = ""
    source_features = ""
    ff_target = ""
    inv = NICPInvariants(ff_source, source_features, ff_target)
    if not inv.is_valid():
        print("Invalid invaris")
        sys.exit(-1)

    matlab_engine = None

    root_path = "."
    all_humans = [f for f in os.listdir(root_path) if osp.isdir(osp.join(root_path, f))]
    for human in all_humans:
        human_folder = osp.join(root_path, human)
        # all_motions = [f for f in os.listdir(human_folder) if osp.isdir(osp.join(human_folder, f))]
        # for motion in all_motions:
        motion = "1"
        current_path = osp.join(root_path, human, motion)
        for base_name in [osp.splitext(fn)[0] for fn in os.listdir(osp.join(current_path, RAW_COLOR_folder))]:
            recon = ReconElement()
            recon.root_path = current_path
            recon.base_name = base_name

            map_file = ""
            recon_exe = ""
            recon_config = ""
            recon.run_face_recon(recon_exe, map_file, recon_config)

            recon.generate_2d_and_3d_landmarks(matlab_engine)

            recon.generate_3dmm_models(matlab_engine)

            nicp_exe = ""
            nicp_options = ""
            calib_matrix = ""
            recon.run_nicp(nicp_exe, nicp_options, inv, calib_matrix)
            print("Job finished at path: %s." % current_path)



