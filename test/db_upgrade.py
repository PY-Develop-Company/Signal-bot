from user_module import none_status

from utils.file_manager import *


def upgrade():
    oldDB = read_file("users/old_db.txt")
    newDB = []
    count = 0
    for user in oldDB:
        new_status = user["status"]

        if new_status == "":
            new_status = none_status

        bufer_user = {
            "id": user["id"],
            "name": user["name"],
            "tag": user["tag"],
            "language": user["language"],
            "status": new_status,
            "acount_number": user["acount_number"],
            "had_trial_status": user["had_trial_status"],
            "trial_end_date": user["trial_end_date"],
            "before_trial_status": user["before_trial_status"]
        }
        newDB.append(bufer_user)
        count += 1

    write_file("users/db.txt", newDB)
    print(count)


upgrade()
# oldDB = read_file("users/old_db.txt")
# for i in oldDB:
#     print(i['tag'])
