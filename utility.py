import json, sqlite3
sqlite3.enable_callback_tracebacks(True)

def getKey():
    with open("setting/key.json", 'r') as f:
        config = json.load(f)
    return config

class timetable:
    def __init__(self):
        self.db = sqlite3.connect("./database/timetable.db")
        self.db.row_factory = sqlite3.Row
        with open(f'./database/schema.sql', 'r') as f:
            self.db.cursor().executescript(f.read())
        self.db.cursor().execute("PRAGMA foreign_keys=ON")
        self.db.commit()