"""
diagnostics.py
Ross Spicer

    module to track errors, warnings, and other diagnostic messages
"""
from pandas import DataFrame
from datetime import datetime


class Diagnostics (object):
    """
    this class keeps track of the errors and such for the model
    """
    
    def __init__ (self):
        """ 
        Class initialiser 
        pre: none
        post: 
            self.messages will be an empty list 
        """
        self.messages = []
        
    def add_message (self, module, type_code, text):
        """
        add a message to the message list
        
        pre: 
            module: is the name of the module where the message originated from
            type_code: what the type of message is
            text: the message
        post: 
            self.messages is appended to 
        """
        message = {}
        message["timestamp"] = datetime.strftime(datetime.now(),
                                                    "%Y-%m-%d %H:%M:%S") 
        message["module"] = module 
        message["type"] = type_code
        message["text"] = text
        self.messages.append(message)
    
    def add_error (self, module, text):
        """
        add an error to the message list
        pre:
            module: is the component were error occurred
            text: the message
        post: 
            self.messages is appended to 
        """
        self.add_message(module, "ERROR", text)
       
    def add_warning (self, module, text):
        """
        add a warning to the message list
        pre:
            module: is the component were warning occurred
            text: the messege
        post: 
            self.messages is appended to 
        """
        self.add_message(module, "WARNING", text)
    
    def add_note (self, module, text):
        """
        add a Note to the message list
        pre:
            module: is the component were note occurred
            text: the messege
        post: 
            self.messages is appended to 
        """
        self.add_message(module, "NOTE", text)
        
    def save_messages (self, file_path):
        """ 
        save messages as csv file
        pre:
            none
        post:
            saved messages as csv file
        """
        try:
            df = DataFrame(self.messages).set_index("timestamp")
            df[["module","type","text"]].to_csv(file_path)
        except KeyError:
            fd = open(file_path, 'w')
            fd.write("No messages were generated...")
            fd.close()
