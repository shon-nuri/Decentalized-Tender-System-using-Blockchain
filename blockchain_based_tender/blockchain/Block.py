import hashlib
import json
from time import time
from datetime import datetime
from django.utils import timezone
from django.db import models
from decimal import Decimal  # Add this import

def serialize_model_data(instance, fields_to_include):
    """
    Serializes a Django model instance into a dictionary containing only specified fields.
    Handles user objects by extracting the username and converts datetime to ISO format.
    """
    data = {}
    for field_name in fields_to_include:
        try:
            value = getattr(instance, field_name)
            
            # Special handling for related objects (like User)
            if hasattr(value, 'username'):
                data[field_name] = value.username
            # Special handling for primary keys (like ForeignKey IDs)
            elif hasattr(value, 'pk'):
                data[field_name] = value.pk
            # Handling datetime objects from either datetime or Django's timezone.datetime
            elif isinstance(value, (datetime, timezone.datetime)):
                data[field_name] = value.isoformat()
            # Handling Decimal objects
            elif isinstance(value, Decimal):
                data[field_name] = float(value)  # Convert Decimal to float for JSON serialization
            # Standard value
            else:
                data[field_name] = value
        except AttributeError:
            data[field_name] = None
    return data


class Block:
    """
    Represents a single block in the chain. 
    Each block stores data (e.g., a Tender or a Bid), a timestamp, 
    a link to the previous block, and its own cryptographic hash.
    """
    def __init__(self, index, timestamp, data, previous_hash=''):
        self.index = index
        self.timestamp = timestamp or time()
        # Data is the payload, e.g., the JSON representation of a Bid or Tender
        self.data = data 
        self.previous_hash = previous_hash
        self.nonce = 0 # Nonce for proof-of-work (simplified)
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Creates a SHA-256 hash of the block's contents.
        """
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        """
        A simplified Proof-of-Work algorithm. Finds a hash that starts 
        with 'difficulty' number of leading zeros.
        """
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"Block Mined! Hash: {self.hash}")

    def to_dict(self):
        """
        Returns a dictionary representation of the Block, suitable for JSON serialization.
        """
        return {
            'index': self.index,
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }
    