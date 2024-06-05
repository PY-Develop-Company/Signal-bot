from enum import Enum


class UserStatusType(Enum):
    deposit_status = "status Deposit"
    trial_status = 'status Trial'
    id_status = "status ID"
    none_status = "status none"
    wait_id_status = 'status wait check ID'
    wait_id_input_status = 'status wait input ID'
    wait_id_input_po_status = 'status wait input ID (POCKET OPTION)'
    wait_id_input_binarium_status = 'status wait input ID (BINARIUM)'
    wait_id_input_iq_cent_status = 'status wait input ID (IQ CENT)'
    wait_deposit_status = 'status wait check Deposit'


class ManagerStatusType(Enum):
    search_id_manager_status = "пошук ID статус"
    search_deposit_manager_status = "пошук депозиту статус"
    none_manager_status = "none"
