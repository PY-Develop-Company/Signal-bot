from file_manager import *
from user_module import *


def printDb():
    DB = read_file("users/db.txt")
    for id, user in enumerate(DB):
        print(f"ID {id}: {user}")


def upgrade():
    oldDB = read_file("users/old_db.txt")
    newDB=[]
    count=0
    nowTime = timeConvertToStr(getNowTime()-timedelta(seconds=7200))
    for user in oldDB:

        bufer_user = {
                    "id": user["id"],
                    "name": user["name"],
                    "tag": user["tag"],
                    "language": user["language"],
                    "status": user['status'],
                    "acount_number": user["acount_number"],
                    "had_trial_status": user["had_trial_status"],
                    "trial_end_date": user["trial_end_date"],
                    "before_trial_status": user["before_trial_status"],
                    "time": nowTime
                }
        newDB.append(bufer_user)
        count += 1

    write_file("users/db.txt", newDB)
    print(count)

# printDb()
# upgrade()

# get_users_group_ids(5,300)
# oldDB = read_file("users/old_db.txt")
# for i in oldDB:
#     print(i['tag'])