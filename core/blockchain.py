
import datetime
import hashlib
from core.nosql import Table, Query
from core.blocks import Block
from core.transactions import Txion
from core.settings import SETTINGS


class Blockchain:
    def __init__(self):
        self._chain = Table('blockchain')
        self._txion = Table('exchanges')

        if len(self._chain.all()) < 1:
            self._create_block(0)

    def _create_block(self, proof):
        """create a new block"""
        index = len(self._chain.all())
        data = self._txion.all() if index > 0 else {'describe': 'initial axiom', 'coins': SETTINGS.COINS}
        timestamp = datetime.datetime.now().strftime(" %d/%m/%Y_%H:%M:%S")
        last_hash = self._chain.all()[index - 1]['hash'] if len(self._chain.all()) > 0 else '[Genesis-Block-0111]'

        b = Block(index=index, data=data, proof=proof, timestamp=timestamp, last_hash=last_hash)
        # todo : check validity

        self._chain.insert(b.__repr__())
        self._txion.truncate()
        return b

    def last_block(self):
        return self._chain.all()[len(self._chain.all()) - 1]

    def block(self, *args):
        b = Query()
        return self._chain.search(b.hash == args[0])[0] if len(self._chain.search(b.hash == args[0])) > 0 else 'None'

    def forge(self):
        """ creating new block by forging()"""

        def valid_proof(last_proof, guessing_value, last_hash):
            """
            Validates the Proof
            :param last_proof: <int> Previous Proof
            :param guessing_value: <int> Current Proof
            :param last_hash: <str> The hash of the Previous Block
            :return: <bool> True if correct, False if not.
            """

            guess = f'{last_proof}{guessing_value}{last_hash}'.encode()
            guess_hash = hashlib.sha256(guess).hexdigest()
            return guess_hash[:4] == "0000"

        def proof_of_work(last_block):
            """
            Simple Proof of Work Algorithm:
             - Find a number p' such that hash(pp') contains leading 4 zeroes
             - Where p is the previous proof, and p' is the new proof

            :param last_block: <dict> last Block
            :return: <int>
            """

            last_proof = last_block['proof']
            last_hash = last_block['hash']

            guessing_proof = 0
            while valid_proof(last_proof, guessing_proof, last_hash) is False:
                guessing_proof += 1

            return guessing_proof

        proof = proof_of_work(self.last_block())
        if proof is not None:
            return self._create_block(proof)

    def synchronise(self, *args, **blockchain):
        """synchronise node with network"""
        print('compute - synchronisation : ' + str(blockchain))
        resolve = False
        resolve_chain = []
        longer_is_self = True

        def compare_blocks(blockchain_one, blockchain_two):
            blockchain_one = blockchain_one.sort()
            blockchain_two = blockchain_two.sort()
            # todo : test with difference : if ain't work : use hash by hash method
            return blockchain_one - blockchain_two, blockchain_one \
                if len(blockchain_one) >= len(blockchain_two) else blockchain_two

        def find_block(key, value, chain):
            for e in chain:
                if e[key] == value:
                    return True
            return False

        if args[0] == 'compute':
            block_difference, longer_chain = compare_blocks(self._chain.all(), blockchain['data'])
            if longer_chain == self._chain.all():
                longer_is_self = True

            if len(block_difference) > 0:
                # check if block_difference in longer_chain : if not -> create resolve chain
                for block in block_difference:
                    if not find_block('hash', block['hash'], longer_chain):
                        resolve_chain.append(block)

                if len(resolve_chain) > 0:
                    resolve_chain += longer_chain
                    resolve_chain.sort(key=lambda x: x['timestamp'])

            if len(resolve_chain) > 0:
                # todo : temporiser resolve_chain -> forge():#next_block
                self._chain.truncate()
                for it in resolve_chain:
                    self._chain.insert(it)

                resolve = False

            if longer_is_self:
                resolve_chain = self._chain.all()

        elif args[0] == 'resolve':
            resolve = True
            resolve_chain = blockchain

            # todo : temporiser resolve_chain -> forge():#next_block
            self._chain.truncate()
            for it in resolve_chain:
                self._chain.insert(it)

        return resolve, resolve_chain

    def exchanges(self, *args, **kwargs):
        """create exchange from the node"""
        expeditor = args[0] if args[0] is not None else None
        to = args[1] if args[1] is not None else None
        obj = args[2] if args[2] is not None else None

        if not expeditor or not to or not obj:
            return 'Error execute exchange.'

        timestamp = datetime.datetime.now().strftime("%d %B %Y %H:%M:%S")
        nounce = self._txion.all()[len(self._txion.all()) - 1]['hash'] if len(self._txion.all()) > 0 else 'empty.nounce'
        tx = Txion(expeditor=expeditor, destinator=to, amount=obj, timestamp=timestamp, nounce=nounce)
        self._txion.insert(tx.__repr__())
        return tx

    def peers_exchanges(self, b_type, item):
        """receiving peers exchanges from network"""
        print('compute - peers_exchanges : ' + str(b_type))
        if b_type == 'block':
            b = Block(**item)
            self._chain.insert(b.__repr__())
        elif b_type == 'txion':
            tx = Txion(**item)
            self._txion.insert(tx.__repr__())

        elif b_type is None:
            print(item)
        else:
            print('unknown item.')

    def __repr__(self):
        return {'blockchain': self._chain.all()}

    def __str__(self):
        return self.__repr__().__str__()
