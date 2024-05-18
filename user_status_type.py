from enum import Enum


class UserStatusType(Enum):
    deposit_status = "status Deposit"
    trial_status = 'status Trial'
    id_status = "status ID"
    none_status = "status none"
    wait_id_status = 'status wait check ID'
    wait_id_input_status = 'status wait input ID'
    wait_deposit_status = 'status wait check Deposit'
