import base58
import codecs
import hashlib
import binascii

from ecdsa import NIST256p, SigningKey

import utils

class Wallet(object):

    def __init__(self):
        #NIST256の楕円曲線暗号を用いて、公開鍵と秘密鍵を作成(キーオブジェクトの状態)
        self._private_key = SigningKey.generate(curve=NIST256p)
        self._public_key = self._private_key.get_verifying_key()
        #公開鍵からブロックチェーンアドレスを生成
        self._blockchain_address = self.generate_blockchain_address()

    @property
    def private_key(self):
        return self._private_key.to_string().hex()
    
    @property
    def public_key(self):
        return self._public_key.to_string().hex()
    
    @property
    def blockchain_address(self):
        return self._blockchain_address
    

    #公開鍵からブロックチェーンアドレスを生成(bpkはbinary public key の略)
    def generate_blockchain_address(self):
        #キーをバイト列に変換 → キーのバイト列をハッシュ化 → ハッシュオブジェクトをバイト列に変換
        public_key_bytes = self._public_key.to_string() 
        sha256_bpk = hashlib.sha256(public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()

        #ripemd160オブジェクト(ハッシュオブジェクト)の生成 → sha256でハッシュ化したバイト列を追加 → 16進数文字列にエンコード(byte型)
        ripemed160_bpk = hashlib.new('ripemd160')
        ripemed160_bpk.update(sha256_bpk_digest)
        ripemed160_bpk_digest = ripemed160_bpk.digest()
        #ここではencodeメソッドはバイト型から16進数表現の文字列というバイト型へのエンコードをしている
        ripemed160_bpk_hex = codecs.encode(ripemed160_bpk_digest, 'hex') #16進数表現の文字列にしたが、実態はbyte型

        # ネットワークバイトの指定(bitcoinでは00) → ネットワークバイトと先ほどのハッシュを結合 →  decodeメソッドにより16進数文字列(バイト型)からバイト列(バイト型)に変換
        network_byte = b'00' #ビットコインと他のネットワークでアドレスを間違わないように先頭にチェーン固有のネットワークバイトを指定する
        network_bitcoin_public_key = network_byte + ripemed160_bpk_hex
        network_bitcoin_public_key_bytes = codecs.decode(network_bitcoin_public_key, 'hex')
        
        #sha256を二回かける → 16進数文字列のバイト列にする
        sha256_bpk = hashlib.sha256(network_bitcoin_public_key_bytes)
        sha256_bpk_digest =  sha256_bpk.digest()
        sha256_2_nbpk = hashlib.sha256(sha256_bpk_digest)
        sha256_2_nbpk_digest = sha256_2_nbpk.digest()
        sha256_hex = codecs.encode(sha256_2_nbpk_digest, 'hex')

        #チェックサムの取得(チェックサムはsha256_hexの先頭の4バイトであり、16進数であらわされているので1バイトが2文字であらわされているから先頭8文字をとる)
        checksum = sha256_hex[:8] 

        #16進数文字列のバイトのnetwork_bitcoin_public_keyとchecksum(おなじく16進数文字列)を足して、utf-8で文字列型にする
        address_hex = (network_bitcoin_public_key + checksum).decode('utf-8')
        print(address_hex)


        #address_hexを16進数の文字列型からバイト型に変換 → base58で文字列のバイト型に変換 → utf-8で文字列に変換
        blockchain_address = base58.b58encode(binascii.unhexlify(address_hex)).decode('utf-8')
        print(binascii.unhexlify(address_hex))
        

        return blockchain_address

class Transaction(object):
    
    def __init__(self, sender_private_key, sender_public_key, sender_blockchain_address, recipient_blockchain_address, value):
        self.sender_private_key = sender_private_key
        self.sender_public_key = sender_public_key
        self.sender_blockchain_address = sender_blockchain_address
        self.recipient_blockchain_address = recipient_blockchain_address
        self.value = value

    def generate_signature(self):
        sha256 = hashlib.sha256()
        transaction = utils.sorted_dict_by_key({
            'sender_blockchain_address': self.sender_blockchain_address,
            'recipient_blockchain_address': self.recipient_blockchain_address,
            'value': float(self.value) 
        })
        sha256.update(str(transaction).encode('utf-8'))
        message = sha256.digest()
        private_key = SigningKey.from_string(
            bytes().fromhex(self.sender_private_key), curve=NIST256p
        )
        private_key_sign = private_key.sign(message)
        signature = private_key_sign.hex()
        
        return signature




if __name__ == '__main__':
    wallet_M = Wallet()
    wallet_A = Wallet()
    wallet_B = Wallet()
    t = Transaction(wallet_A.private_key, wallet_A.public_key, wallet_A.blockchain_address, wallet_B.blockchain_address, 1.0)

    ######################## Blockchain Node
    import blockchain
    block_chain = blockchain.BlockChain(blockchain_address=wallet_M.blockchain_address)
    is_added = block_chain.add_transaction(
        wallet_A.blockchain_address,
        wallet_B.blockchain_address,
        1.0,
        wallet_A.public_key,
        t.generate_signature()
    )
    print("Added?", is_added)
    block_chain.mining()
    utils.pprint(block_chain.chain)

    print('A', block_chain.calculate_total_amount(wallet_A.blockchain_address))
    print('B', block_chain.calculate_total_amount(wallet_B.blockchain_address))
    print('M', block_chain.calculate_total_amount(wallet_M.blockchain_address))


    
