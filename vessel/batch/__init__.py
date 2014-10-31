from batch.fetch_container_vessel_data import FetchContainerVesselData
from batch.fetch_user_fleets_data import FetchUserFleetsData

def start():
    FetchUserFleetsData().run()
    FetchContainerVesselData().run()
