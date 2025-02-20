from uuid import uuid4
import threading
from pymongo import MongoClient
from pymongo.collection import Collection


class SessionMemory():
    def __init__(self, session_id: str = None):
        if session_id is None:
            session_id = str(uuid4())[:8]
        self.session_id = session_id
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["aws-agent-session-memory"]

        self.notes = []
        self.tasks = []
        self.load_notes()

    def load_notes(self):
        self.notes = list(self.db["notes"].find({"session_id": self.session_id}))

    def save_notes(self):
        self.db["notes"].delete_many({"session_id": self.session_id})
        self.db["notes"].insert_many([{"session_id": self.session_id, "text": note} for note in self.notes])

    def load_tasks(self):
        self.tasks = list(self.db["tasks"].find({"session_id": self.session_id}))
    
    def save_tasks(self):
        self.db["tasks"].delete_many({"session_id": self.session_id})
        self.db["tasks"].insert_many([{"session_id": self.session_id, "text": note} for note in self.tasks])


    def add_note(self, note):
        self.notes.append(dict(id=str(uuid4())[:8], text=note))

    def get_notes(self):
        return self.notes or []
    
    def get_messages(self):
        return list(self.db["messages"].find({"session_id": self.session_id}))
    
    def add_message(self, role, content):
        self.db["messages"].insert_one({"session_id": self.session_id, "role": role, "content": content})

    def get_working_dir(self):
        result = self.db["environment"].find_one({"session_id": self.session_id})
        if result:
            return result["working_dir"]
        return None

    def set_working_dir(self, working_dir):
        self.db["environment"].update_one({"session_id": self.session_id}, {"$set": {"working_dir": working_dir}}, upsert=True)


# Lazy initialization with thread-safety
_session_memory = None
_lock = threading.Lock()

def get_session_memory(session_id=None)->SessionMemory:
    global _session_memory
    if _session_memory is None:
        with _lock:  # Ensures thread-safe initialization
            if _session_memory is None:  # Double-checked locking
                _session_memory = SessionMemory(session_id)
    return _session_memory