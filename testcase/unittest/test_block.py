#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test Block functions"""

import logging
import json
import sys
import unittest

import loopchain.utils as util
import testcase.unittest.test_util as test_util

from cli_tools.icx_test.icx_wallet import IcxWallet
from loopchain import configure as conf
from loopchain.baseservice import ObjectManager
from loopchain.blockchain.validator import tx_validator, IconValidateStrategy, get_tx_hash_generator
from testcase.unittest.mock_peer import set_mock

sys.path.append('../')
from loopchain.blockchain import Block, BlockInValidError, Transaction
from loopchain.utils import loggers

loggers.set_preset_type(loggers.PresetType.develop)
loggers.update_preset()


class TestBlock(unittest.TestCase):
    __peer_id = 'aaa'

    def setUp(self):
        conf.ENABLE_USER_CONFIG = False
        conf.Configure().init_configure()
        test_util.print_testname(self._testMethodName)
        self.peer_auth = test_util.create_default_peer_auth()
        set_mock(self)

    def tearDown(self):
        ObjectManager().peer_service = None

    def __generate_block_data(self) -> Block:
        """ block data generate
        :return: unsigned block
        """
        genesis = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)
        genesis.generate_block()
        # Block 생성
        block = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)
        # Transaction(s) 추가
        for x in range(0, 10):
            block.put_transaction(test_util.create_basic_tx(self.__peer_id, self.peer_auth))

        # Hash 생성 이 작업까지 끝내고 나서 Block을 peer에 보낸다
        block.generate_block(genesis)
        return block

    def __generate_block(self) -> Block:
        """ block data generate, add sign
        :return: signed block
        """
        block = self.__generate_block_data()
        block.sign(self.peer_auth)
        return block

    def __generate_invalid_block(self) -> Block:
        """ create invalid signature block
        :return: invalid signature block
        """
        block = self.__generate_block_data()
        block._Block__signature = b'invalid signature '
        return block

    def test_put_transaction(self):
        """
        Block 에 여러 개 transaction 들을 넣는 것을 test.
        """
        block = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)
        tx_list = []
        tx_size = 10
        for x in range(0, tx_size):
            tx = test_util.create_basic_tx(self.__peer_id, self.peer_auth)
            tx2 = test_util.create_basic_tx(self.__peer_id, self.peer_auth)
            tx_list.append(tx2)
            self.assertNotEqual(tx.tx_hash, "", "트랜잭션 생성 실패")
            self.assertTrue(block.put_transaction(tx), "Block에 트랜잭션 추가 실패")
        self.assertTrue(block.put_transaction(tx_list), "Block에 여러 트랜잭션 추가 실패")
        self.assertEqual(block.confirmed_tx_len, tx_size * 2, "트랜잭션 사이즈 확인 실패")

    @unittest.skip
    def test_validate_block(self):
        """ GIVEN correct block and invalid signature block
        WHEN validate two block
        THEN correct block validate return True, invalid block raise exception
        """
        # GIVEN
        # create correct block
        block = self.__generate_block()
        # WHEN THEN
        self.assertTrue(Block.validate(block), "Fail to validate block!")

        # GIVEN
        # create invalid block
        invalid_signature_block = self.__generate_invalid_block()

        # WHEN THEN
        with self.assertRaises(BlockInValidError):
            Block.validate(invalid_signature_block)

    def test_transaction_merkle_tree_validate_block(self):
        """
        머클트리 검증
        """
        # 블럭을 검증 - 모든 머클트리의 내용 검증
        block = self.__generate_block_data()
        mk_result = True
        for tx in block.confirmed_transaction_list:
            # FIND tx index
            idx = block.confirmed_transaction_list.index(tx)
            sm_result = Block.merkle_path(block, idx)
            mk_result &= sm_result
            # logging.debug("Transaction %i th is %s (%s)", idx, sm_result, tx.tx_hash)
        # logging.debug("block mekletree : %s ", block.merkle_tree)
        self.assertTrue(mk_result, "머클트리검증 실패")

    def test_serialize_and_deserialize(self):
        """
        블럭 serialize and deserialize 테스트
        """
        block = self.__generate_block()
        test_dmp = block.serialize_block()
        block2 = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)
        block2.deserialize_block(test_dmp)
        logging.debug("serialize block hash : %s , deserialize block hash %s",
                      block.merkle_tree_root_hash, block2.merkle_tree_root_hash)
        self.assertEqual(block.merkle_tree_root_hash, block2.merkle_tree_root_hash, "블럭이 같지 않습니다 ")

    def test_block_rebuild(self):
        """ GIVEN 1Block with 3tx, and conf remove failed tx when in block
        WHEN Block call verify_through_score_invoke
        THEN all order 3tx must removed in block
        """
        block = Block(conf.LOOPCHAIN_DEFAULT_CHANNEL)
        fail_tx_hash = None
        for i in range(3):
            tx = Transaction()
            tx.put_meta(Transaction.CHANNEL_KEY, conf.LOOPCHAIN_DEFAULT_CHANNEL)
            tx.put_data("aaaaa")
            tx.sign_hash(self.peer_auth)
            block.put_transaction(tx)
            if i == 2:
                fail_tx_hash = tx.tx_hash
        verify, need_rebuild, invoke_results = block.verify_through_score_invoke(True)
        self.assertTrue(need_rebuild)
        logging.debug(f"fail tx hash : {fail_tx_hash}")
        self.assertEqual(block.confirmed_tx_len, 2)
        for i, tx in enumerate(block.confirmed_transaction_list):
            self.assertNotEqual(i, 2, "index 2 must be deleted")
            self.assertNotEqual(tx.tx_hash, fail_tx_hash)

    def test_block_hash_must_be_the_same_regardless_of_the_commit_state(self):
        # ENGINE-302
        # GIVEN
        block1 = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)
        block2 = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)

        # WHEN
        block1.commit_state = {"TEST": "TEST_VALUE1234"}
        block1.generate_block()
        block2.generate_block()
        util.logger.spam(f"block1 hash({block1.block_hash})")
        util.logger.spam(f"block1 hash({block2.block_hash})")

        # THEN
        self.assertEqual(block1.block_hash, block2.block_hash)

    def test_block_prevent_tx_duplication(self):
        origin_send_tx_type = conf.CHANNEL_OPTION[conf.LOOPCHAIN_DEFAULT_CHANNEL]["send_tx_type"]
        conf.CHANNEL_OPTION[conf.LOOPCHAIN_DEFAULT_CHANNEL]["send_tx_type"] = conf.SendTxType.icx
        tx_validator.refresh_tx_validators()

        try:
            block = Block(channel_name=conf.LOOPCHAIN_DEFAULT_CHANNEL)

            client = IcxWallet()
            client.to_address = 'hxebf3a409845cd09dcb5af31ed5be5e34e2af9433'
            client.value = 1

            hash_generator = get_tx_hash_generator(conf.LOOPCHAIN_DEFAULT_CHANNEL)
            validator = IconValidateStrategy(hash_generator)
            icx_origin = client.create_icx_origin()
            for i in range(10):
                tx = validator.restore(json.dumps(icx_origin), 'icx/score')
                block.put_transaction(tx)

            block.generate_block()
            self.assertEqual(block.confirmed_tx_len, 1)
        finally:
            conf.CHANNEL_OPTION[conf.LOOPCHAIN_DEFAULT_CHANNEL]["send_tx_type"] = origin_send_tx_type
            tx_validator.refresh_tx_validators()


if __name__ == '__main__':
    unittest.main()
