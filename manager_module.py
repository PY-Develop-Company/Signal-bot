from user import *
from user_status_type import ManagerStatusType
from db_modul import *

from my_debuger import debug_error, debug_info


class ManagerUser(GenericUser):
    def __init__(self, id, full_name, tag):
        super().__init__(id, full_name, tag)

        self.status = ManagerStatusType.none_manager_status.value
        self.do = "none"

        if not self.load_user():
            self.add_user(id, full_name, tag)
            self.load_user()

    def add_user(self, id, full_name, tag):
        cursor = db_connection.cursor()
        cursor.execute(f'''INSERT INTO {manager_table} (id, status, do, language) VALUES (?, ?, ?, ?)''',
                       (self.id, self.status, self.do, self.language))
        db_connection.commit()

    def load_user(self):
        user_data = self.find_user_with_id(self.id)

        if user_data is None:
            return False

        self.id = user_data["id"]
        self.status = user_data["status"]
        self.do = user_data["do"]
        self.language = user_data["language"]

        return True

    @staticmethod
    def find_user_with_id(id):
        cursor = db_connection.cursor()
        cursor.execute(f"SELECT id, status, do, language FROM {manager_table} WHERE id = ?", (id,))
        existing_user = cursor.fetchone()

        if existing_user is None:
            return None

        user_dict = {
            "id": existing_user[0],
            "status": existing_user[1],
            "do": existing_user[2],
            "language": existing_user[3],
        }

        return user_dict

    def set_language(self, new_language):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"UPDATE {manager_table} SET language = ? WHERE id = ?", (new_language, self.id))
            db_connection.commit()
            self.language = new_language
        except sqlite3.Error as error:
            debug_error(error, f"Error set language manager {self.id}")

    def set_do(self, do):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"UPDATE {manager_table} SET do = ? WHERE id = ?", (do, self.id))
            db_connection.commit()
            self.do = do
        except sqlite3.Error as error:
            debug_error(error, f"Error updating manager's 'do'")

    def set_status(self, status: ManagerStatusType):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"UPDATE {manager_table} SET status = ? WHERE id = ?", (status.value, self.id))
            db_connection.commit()
            self.status = status.value
        except sqlite3.Error as error:
            debug_error(error, f"Error updating manager's 'status'")

    def get_do_account_number(self):
        user = User(self.do, None, None)
        account = Account.get_by_id(user.account_id)
        return account.id, account.type, user

    def has_status(self, status: ManagerStatusType):
        return self.status == status.value
