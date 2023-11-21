# https://pypi.org/project/python-synology/


import synology_dsm

from synology_dsm import SynologyDSM

@service
def shutdown():
    api = SynologyDSM(dsm_ip="192.168.178.22", dsm_port="5000", username="home_assistant", password="udUD90BB", session="false")
    system = api.system
    system.shutdown()