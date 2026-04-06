import json
import os

class HistoryStack:
    def __init__(self, items=None):
        if items is None:
            self.items = []
        else:
            self.items = items
            
    def push(self, transaction):
        self.items.append(transaction)
        
    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None
        
    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None
        
    def is_empty(self):
        return len(self.items) == 0
        
    def get_all(self):
        # return items reversed (LIFO style for displaying history)
        return self.items[::-1]

def load_user_history_stack(history_file, username):
    if not os.path.exists(history_file):
        return HistoryStack([])
    try:
        with open(history_file, 'r') as f:
            data = json.load(f)
            return HistoryStack(data.get(username, []))
    except:
        return HistoryStack([])

def save_user_history_stack(history_file, username, stack):
    data = {}
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                data = json.load(f)
        except:
            pass
    
    data[username] = stack.items
    
    with open(history_file, 'w') as f:
        json.dump(data, f, indent=4)
