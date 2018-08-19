import time
import hashlib
import random
import string
import json
from threading import Thread
from decimal import Decimal



#区块类
class Block(object):
    def __init__(self):
        self.index = None  #区块id
        self.hash = None
        self.previous_hash = None
        self.nonce = None
        self.difficulty = None
        self.timestamp = None
        self.transaction_data = None

    #用字典格式存储区块信息，并返回区块字典
    def get_block_info(self):
        block_info = {
            'Index':self.index,
            'Hash':self.hash,
            'Previous_hash':self.previous_hash,
            'Nonce':self.nonce,
            'Difficulty':self.difficulty,
            'Timestamp':self.timestamp,
            'Transaction_data':self.transaction_data,
        }
        return block_info

#矿工类
class Pitman(object):
    def mine(self,index,previous_hash,transaction_data):
        print('begin mine!')
        begin_time = time.time()
        block = Block()
        block.index = index
        block.previous_hash = previous_hash
        block.transaction_data = transaction_data
        block.timestamp = time.time()
        block.difficulty,block.hash,block.nonce = self.gen_hash(previous_hash,transaction_data)
        end_time = time.time()
        spend_time = end_time - begin_time
        print('mine finish')
        return block,spend_time

    @staticmethod
    def gen_hash(previous_hash,transaction_data):
        nonce = random.randrange(1,99999)
        difficulty = 0
        guess = str(previous_hash)+str(nonce)+transaction_data
        res = hashlib.sha256(guess.encode()).hexdigest()

        # 验证id是否符合要求，本案例中设定以00开头
        while res[0:1] !='00':
            #每尝试一次，上调一位难度系数
            difficulty = difficulty +1
            nonce = nonce+difficulty
            guess = previous_hash + str(nonce) + transaction_data
            res = hashlib.sha256(guess.encode()).hexdigest()
        # 得到符合要求的id后，返回难度系数，id值和随机数
        return difficulty,res,nonce

#线程类
class MyThread(Thread):
    def __init__(self,target,args=()):
        super(MyThread,self).__init__()
        self.func = target
        self.arg = args

    def run(self):
        self.result = self.func(*self.arg)

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            print('自定义线程获取结果时发生错误',e)

class BlockChain(object):
    def __init__(self,hash_num):
        # 存储区块链对象，区块的容器
        self.chain_list = []
        self.pitman_list = []
        for i in range(2):
            self.pitman_list.append(Pitman)
        self.result_list = []
        self.gen_block(hash_num)

    @property
    def get_last_block(self):
        if len(self.chain_list):
            return self.chain_list[-1]
        return None

    def get_trans(self):
        dict_data = {
            'sender':''.join(random.sample(string.ascii_letters+string.digits,8)),
            'recipient':''.join(random.sample(string.ascii_letters+string.digits,8)),
            'amount':random.randrange(1,10000),
        }
        return json.dumps(dict_data)

    def gen_block(self,initial_hash = None):
        # 创世区块
        if initial_hash:
            block = Block()
            block.index = 0
            block.nonce = random.randrange(0,99999)
            # 创世区块，之前没有值，故为00
            block.previous_hash = '00'
            block.difficulty = 0
            block.transaction_data = self.get_trans()
            guess = str(block.index) + str(block.nonce) +block.previous_hash
            block.hash = hashlib.sha256(guess.encode()).hexdigest()
            block.timestamp = time.time()
            self.chain_list.append(block)
        else:
            #先启动矿工开始挖矿
            for pitman in self.pitman_list:
                t = MyThread(target=pitman.mine,args=(pitman,
                                                      len(self.chain_list),
                                                      # 获取当前这个区块链的最好一个区块的id
                                                      self.get_last_block.get_block_info()['Hash'],
                                                      # 获取交易信息
                                                      self.get_trans()))
                t.start()
                t.join()
                self.result_list.append(t.get_result())
            #t.get_result()返回一个列表，列表第一项是block，第二项是spend_time
            #两个线程运行完毕结束循环，用时最短的矿工挖出来的区块为下一区块
            for result in self.result_list:
                print(result[0].get_block_info())
            first_block = self.result_list[0][0]
            min_time = Decimal(self.result_list[0][1])
            #冒泡排序，找到用时最短的区块
            for i in range(1,len(self.result_list)):
                if Decimal(self.result_list[i][1]) < min_time:
                    first_block = self.result_list[i][0]
            #找到以后存储
            self.chain_list.append(first_block)
            #清空结果列表
            self.result_list = []
    def show_chain(self):
        for block in self.chain_list:
            print(block.get_block_info())

if __name__=='__main__':
    chain = BlockChain(1)
    for i in range(20):
        chain.gen_block()
    chain.show_chain()