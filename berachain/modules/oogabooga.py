from modules.utils import sleeping, logger
from modules.wallet import Wallet
import settings
from .config import TOKEN_ADDRESSES


class OogaBooga(Wallet):
    def __init__(self, wallet: Wallet):
        super().__init__(privatekey=wallet.privatekey, tg_report=wallet.tg_report, browser=wallet.browser)

        self.from_chain = 'berachain'
        self.web3 = self.get_web3(self.from_chain)

        self.mint()


    def mint(self, retry=0):
        try:
            module_str = f'mint OogaBooga Ticket'

            old_balance = self.get_balance(chain_name='berachain', token_name='OOGABOOGA')

            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(TOKEN_ADDRESSES['OOGABOOGA']),
                abi='[{"inputs":[],"name":"buy","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"mintCost","outputs":[{"internalType":"uint256","name":"native","type":"uint256"},{"internalType":"uint256","name":"erc20","type":"uint256"}],"stateMutability":"view","type":"function"}]'
            )

            cost = contract.functions.mintCost().call()[1]
            honey_balance = self.get_balance(chain_name=self.from_chain, token_name='HONEY')
            if cost > honey_balance:
                raise Exception(f'Not enough HONEY to mint OogaBooga Ticket: {round(honey_balance / 1e18, 2)}')

            self.approve(chain_name=self.from_chain, spender=contract.address, token_name='HONEY', value=cost)

            contract_txn = contract.functions.buy()

            tx_hash = self.sent_tx(chain_name=self.from_chain, tx=contract_txn, tx_label=module_str)
            if self.wait_balance(chain_name='berachain', token_name='OOGABOOGA', needed_balance=old_balance, only_more=True) == 'not updated':
                if retry < settings.RETRY:
                    return self.mint(retry=retry+1)
                else:
                    self.tg_report.update_logs(f'❌ {module_str}: balance not updated')
                    raise ValueError(f'{module_str}: balance not updated')
            return tx_hash

        except Exception as error:
            if retry < settings.RETRY and not 'Not enough HONEY' in str(error):
                logger.error(f'{module_str} | {error}')
                sleeping(10)
                return self.mint(retry=retry+1)
            else:
                self.tg_report.update_logs(f'❌ {module_str}: {error}')
                raise ValueError(f'{module_str}: {error}')
