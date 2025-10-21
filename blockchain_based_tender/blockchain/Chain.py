from .Block import Block
from time import time
import json
import os

class Blockchain:
    """
    Manages the chain of blocks. Stores the chain in a simple JSON file for persistence.
    """
    def __init__(self, chain_file='blockchain_data.json', difficulty=2, genesis_data=None):
        self.chain = []
        

        self.difficulty = difficulty
        self.chain_file = chain_file

        self.load_chain()

    def create_genesis_block(self):
        """
        The first block in the chain.
        """
        genesis_block = Block(0, time(), "Genesis Block", "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)

    def get_latest_block(self):
        """
        Returns the most recently added block.
        """
        if self.chain:
            return self.chain[-1]
        return None

    def add_block(self, new_data):
        """
        Creates a new block, mines it, and adds it to the chain.
        """
        latest_block = self.get_latest_block()
        new_index = 0
        previous_hash = '0'
        
        if latest_block:
            new_index = latest_block.index + 1
            previous_hash = latest_block.hash

        new_block = Block(new_index, time(), new_data, previous_hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.save_chain()
        return new_block

    def is_chain_valid(self):
        """
        Verifies the integrity of the entire chain by checking hash links.
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # 1. Check if the block's hash is correct (re-calculating the hash)
            if current_block.hash != current_block.calculate_hash():
                return False

            # 2. Check if it links to the correct previous block
            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def save_chain(self):
        """
        Saves the chain to a JSON file.
        """
        serializable_chain = []
        for block in self.chain:
            serializable_chain.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'data': block.data,
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            })
        
        with open(self.chain_file, 'w') as f:
            json.dump(serializable_chain, f, indent=4)

    def load_chain(self):
        """
        Loads the chain from the JSON file. Creates Genesis block if file not found.
        """
        if os.path.exists(self.chain_file) and os.path.getsize(self.chain_file) > 0:
            try:
                with open(self.chain_file, 'r') as f:
                    raw_chain = json.load(f)
                
                self.chain = []
                for block_data in raw_chain:
                    block = Block(
                        block_data['index'], 
                        block_data['timestamp'], 
                        block_data['data'], 
                        block_data['previous_hash']
                    )
                    block.hash = block_data['hash']
                    block.nonce = block_data['nonce']
                    self.chain.append(block)
                print(f"Blockchain loaded with {len(self.chain)} blocks.")
                
            except (json.JSONDecodeError, KeyError, IndexError):
                print("Error loading chain. Creating new Genesis block.")
                self.create_genesis_block()
        else:
            print("No blockchain data found. Creating Genesis block.")
            self.create_genesis_block()

    def to_list_of_dicts(self):
        """
        Returns the chain as a list of dictionaries.
        """
        serializable_chain = []
        for block in self.chain:
            serializable_chain.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'data': block.data,
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            })
        return serializable_chain
    
    @classmethod
    def load_from_list_of_dicts(cls, chain_list, chain_file='blockchain_data.json', difficulty=2):
        """
        Creates a Blockchain instance from a list of block dictionaries.
        """
        blockchain = cls(chain_file=chain_file, difficulty=difficulty)
        blockchain.chain = []
        for block_data in chain_list:
            block = Block(
                block_data['index'],
                block_data['timestamp'],
                block_data['data'],
                block_data['previous_hash']
            )
            block.hash = block_data['hash']
            block.nonce = block_data['nonce']
            blockchain.chain.append(block)
        return blockchain

# Global instance of the Blockchain for easy access across the Django app
tender_blockchain = Blockchain(chain_file='tender_blockchain.json', difficulty=4)
