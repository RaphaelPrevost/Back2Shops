from B2SProtocol.constants import CustomEnum


class VESSEL_STATUS:
    MOORED = 'moored'

class CONTAINER_STATUS:
    LOADED_AT_FIRST_POL = 'Loaded at First POL'

    #ARRIVED_AT_TS_POD = 'Arrived at T/S POD'
    #DISCHARGING_AT_TS_POD = 'Discharging'
    DISCHARGED_AT_TS_POD = 'Discharged at T/S POD'
    LOADED_AT_TS_POL = 'Loaded at T/S POL'

    #ARRIVED_AT_LAST_POD = 'Arrived at Last POD'
    #DISCHARGING_AT_LAST_POD = 'Discharging'
    DISCHARGED_AT_LAST_POD = 'Discharged at Last POD'
