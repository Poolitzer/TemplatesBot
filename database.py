import json


class Database:
    def __init__(self):
        self.db = json.load(open("./database.json"))

    def get_user(self, user_id):
        try:
            return self.db["users"][str(user_id)]
        except KeyError:
            return None

    def get_users(self):
        temp = ""
        for x in self.db["users"]:
            temp = temp + ", " + x
        return temp

    def get_all_users(self):
        to_return = []
        for user in self.db["users"]:
            to_return.append([user, self.db["users"][str(user)]])
        return to_return

    def get_banned(self):
        temp = ""
        for x in self.db["banned"]:
            temp = temp + ", " + str(x)
        return temp

    def insert_user(self, user_id, languages):
        try:
            self.db["users"][str(user_id)]["langcodes"] = languages
        except KeyError:
            self.db["users"][str(user_id)] = {"langcodes": languages, "custom": [], "custom_pre": [], "custom_post": []}
        self.save()

    def insert_banned_user(self, user_id):
        self.db["banned"].append(int(user_id))
        self.save()

    def insert_custom(self, user_id, custom):
        self.db["users"][str(user_id)]["custom"] = custom
        self.save()

    def insert_custom_overrides(self, user_id, pre=None, post=None):
        self.db["users"][str(user_id)]["custom_pre"] = []
        self.db["users"][str(user_id)]["custom_post"] = []
        if pre:
            self.db["users"][str(user_id)]["custom_pre"] = pre
        if post:
            self.db["users"][str(user_id)]["custom_post"] = post
        self.save()

    def save(self):
        with open('./database.json', 'w') as outfile:
            json.dump(self.db, outfile, indent=4, sort_keys=True)

    @staticmethod
    def to_file(string, user_id):
        with open(f"templates/tl_{user_id}.txt", "w", encoding='UTF-8') as text_file:
            text_file.write(string)


database = Database()
