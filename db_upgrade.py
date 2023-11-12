from file_manager import *


# new STATUSES
new_deposit_status = "status Deposit"
new_wait_id_status = 'status wait check ID'
new_wait_id_input_status = 'status wait input ID'
new_wait_deposit_status = 'status wait check Deposit'
none_status = "status none"

#old status
deposit_status = "status ДЕПОЗИТ"
wait_id_status = 'Ожидайте проверку ID ⏳'
wait_id_input_status = 'Ожидание ввода проверки ID 🔖'
wait_deposit_status = 'Ожидание проверки депозита 💵'


def upgrade():
    oldDB = read_file("users/old_db.txt")
    newDB=[]
    count=0
    for user in oldDB:
        bufer_status =""
        if user["status"]== deposit_status:
            bufer_status=new_deposit_status
        elif user["status"]== wait_id_status:
            bufer_status=new_wait_id_status
        elif user["status"]== wait_id_input_status:
            bufer_status=new_wait_id_input_status
        elif user["status"]== wait_deposit_status:
            bufer_status=new_wait_deposit_status

        bufer_user = {
                    "id": user["id"],
                    "name": user["name"],
                    "language": "none",
                    "status": bufer_status,
                    "acount_number": user["acount_number"],
                    "had_trial_status": False,
                    "trial_end_date": None,
                    "before_trial_status": none_status
                }
        newDB.append(bufer_user)
        count+=1
    write_file("users/db.txt",newDB)
    print(count)

upgrade()