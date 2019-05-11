from NonRigidICP.NonRigidICP import NonRigidICP
from Fit3DMM.fit_3dmm import generate_3dmm_params

if __name__ == "__main__":
    mission = NonRigidICP()
    mission.load_from_json_file(".\\test.json")
    mission.pretreatment()
    mission.run()
    print(1)


    list = []

    for k in list:
        continue
