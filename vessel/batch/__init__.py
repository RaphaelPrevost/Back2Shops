from batch.fetch_container_data import FetchContainerData
from batch.fetch_vessel_data import FetchVesselData

def start():
    FetchVesselData().run()
    FetchContainerData().run()
