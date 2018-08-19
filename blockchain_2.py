import hashlib
import json
import requests
from time import time
from uuid import uuid4
from textwrap import dedent
from flask import Flask, jsonify, request
from urllib.parse import urlparse

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        #创建创始块
        self.new_block(previous_hash=1,proof=100)
        self.nodes = set()  #用set储存节点，避免重复添加节点
    def register_node(self,address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    def new_block(self,proof,previous_hash=None):
        block = {
            'index':len(self.chain)+1,
            'timestamp':time(),
            'transactions':self.current_transactions,
            'proof':proof,
            'previous_hash':previous_hash or self.hash(self.chain[-1]),
        }
        #重置交易列表
        self.current_transactions = []
        self.chain.append(block)
        return block
    def new_transcation(self,sender,recipient,amount):
        """
        创建一个交易进入进入下一个挖矿块
        发送者参数：发送者地址，字符串
        接收者参数：接受者地址，字符串
        数量参数：<int>
        返回值：<存储该交易信息的区块索引>
        """
        self.current_transactions.append(
            {'sender':sender,
             'recipient':recipient,
             'amount':amount,
             }
        )
        return self.last_block['index']+1
    @staticmethod
    def hash(block):
        #将字典转化为json字符串，用sha256的方法加密
        block_string = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    @property
    def last_block(self):
        return self.chain[-1]
    def proof_of_work(self,last_proof):
        #工作量证明
        proof = 0
        while self.valid_proof(last_proof,proof) is False:
            proof += 1
        return proof
    @staticmethod
    def valid_proof(last_proof,proof):
        #校验guess的hash值是否为0000起头的字符串，返回布尔值
        #格式化字符串的一种写法，等同于(str(last_proof)+str(proof)).encode()
        #此处，proof应为nonce,那么，nonce+transactions+previous_hash经sha256算法加密后为current_hash，该处与理论不符
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'
    def valid_chain(self,chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n-------------------------\n')
            #检查该区块的前一区块的hash值与上一块的hash结果是否一致
            if block['previous_hash'] != self.hash(last_block):
                return False
            #调用valid_proof检测hash值是否满足特定的形式
            if not self.valid_proof(last_block['proof'],block['proof']):
                return False
            last_block = block
            current_index += 1
        return True
    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        #寻找比自己链还要长的链
        max_length = len(self.chain)
        #爬取并验证网络中所有节点中链
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                #寻找最长链，并验证该链是否有效
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # 假如发现了一条新链，验证这条链长于我们的链
        if new_chain:
            #改变链
            self.chain = new_chain
            return True
        return False


#实例化节点
app = Flask(__name__)
#为该节点生成一个全局唯一的地址
node_identifier = str(uuid4()).replace('-','')
#实例化区块链类
blockchain = Blockchain()

#只做三件事：计算PoW；通过新增一个交易授予矿工一定数量的coin；构造新的区块并将其添加到区块链中
@app.route('/mine',methods=['GET'])
def mine():
    #工作量证明算法得到新的proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    #给找到证明的人发放一个coin的奖励
    #发送者是"0"，表示这个节点挖出一个新的coin
    blockchain.new_transcation(
        sender="0",
        recipient=node_identifier,
        amount=1
    )
    #将新块添加在区块链的尾部
    block = blockchain.new_block(proof)
    #返回响应
    response = {
        'message':'New Block Forged',
        'index':block['index'],
        'transactions':block['transactions'],
        'proof':block['proof'],
        'previous_hash':block['previous_hash'],
    }
    return jsonify(response),200

@app.route('/transactions/new',methods=['POST'])
def new_transaction():
    values = request.get_json()
    #检查POST方法传递的数据是否包含需要的值
    required = ['sender','recipient','amount']
    if not all(k in values for k in required):
        return 'Missing values',400
    #创建一个新的交易
    index = blockchain.new_transcation(values['sender'],values['recipient'],values['amount'])
    response = {'message':f'Transaction will be added to Block {index}'}
    return jsonify(response),201

@app.route('/chain',methods=['GET'])
def full_chain():
    #返回json字符串形式的相应以及http状态码200
    response = {
        'chain':blockchain.chain,
        'length':len(blockchain.chain),
    }
    return jsonify(response),200

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000)


