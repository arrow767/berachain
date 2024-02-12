from random import shuffle
import os

from modules import *
from settings import SLEEP_BETWEEN_ACCS, SHUFFLE_WALLETS, ONLY_FAUCET_GALXE


def berachain_onchain(wallet: Wallet, email: Rambler):

    # request funds
    bera_balance = wallet.get_balance(chain_name='berachain')
    if bera_balance == 0:
        wallet.browser.request_faucet(address=wallet.address)
        if wallet.wait_balance(chain_name='berachain', needed_balance=0, only_more=True) == 'not updated':
            raise Exception(f'[-] Web3 | Tokens not arrived from Faucet')
    else:
        logger.info(f'[+] Web3 | This wallet already has {round(bera_balance / 1e18, 2)} BERA')

    # swap tokens to $honey
    honey_balance = wallet.get_balance(chain_name='berachain', token_name='HONEY')
    if honey_balance / 1e18 > 4.2:
        logger.info(f'[+] Web3 | This wallet already has {round(honey_balance / 1e18, 2)} HONEY')
    else:
        Bex(wallet=wallet) # BERA -> stgUSDC
        sleeping(1, 5) # задержка между свапами
        Honey(wallet=wallet) # stgUSDC -> HONEY
        sleeping(1, 5)  # задержка после свапов

    # mint ooga booga ooga booga
    if wallet.get_balance(chain_name='berachain', token_name='OOGABOOGA') > 0:
        logger.info(f'[+] Web3 | This wallet already minted OogaBooga Ticket')
        return '✅ OogaBooga Ticket already minted'
    elif wallet.get_balance(chain_name='berachain', token_name='HONEY', human=True) > 4.2:
        OogaBooga(wallet=wallet)
        return '✅ OogaBooga Ticket minted'
    else:
        logger.error(f'[+] Web3 | Not enough funds to mint OogaBooga Ticket')
        return '❌ Not enough funds to mint OogaBooga Ticket'


def galxe_quests_confirm(wallet: Wallet, email: Rambler):
    signature, text = wallet.get_signature_for_galxe_login()

    wallet.browser.login_in_galxe(address=wallet.address, text=text, signature=signature)
    galxe_acc_info = wallet.browser.get_galaxy_acc_info()

    if galxe_acc_info["email"] == "":
        if email.mail_data == None: raise Exception(f'[-] Galxe | This wallet doesnt have bound email. You must provide it in .txt for this account')
        wallet.browser.send_email(email=email.mail_login)
        code = email.get_code()
        wallet.browser.confirm_email(email=email.mail_login, code=code)
    else:
        logger.info(f'[+] Galxe | Already bound email "{galxe_acc_info["email"]}"')

    if ONLY_FAUCET_GALXE:
        # faucet
        faucet_status = wallet.browser.complete_quest(task_name='faucet')
        points = wallet.browser.get_points_amount()

        if '✅' in faucet_status:
            return f'{faucet_status} from faucet. Total points: {points}'
        else:
            return f'❌ {faucet_status}. Total points: {points}'

    else:
        completed = 0
        # faucet
        if wallet.browser.complete_quest(task_name='faucet') == True: completed += 1

        # visit proof of liquidity page
        if wallet.browser.complete_quest(task_name='proof_of_liq') == True: completed += 1

        # bera docs
        if wallet.browser.complete_quest(task_name='docs') == True: completed += 1
        # quiz
        if wallet.browser.complete_quest(task_name='quiz') == True: completed += 1

        # drip $bera
        if wallet.browser.complete_quest(task_name='drip_bera') == True: completed += 1

        # swap bera - usdc
        if wallet.browser.complete_quest(task_name='swap_bera') == True: completed += 1

        # mint honey
        if wallet.browser.complete_quest(task_name='mint_honey') == True: completed += 1

        try: wallet.browser.claim_campaign(task_name='March of the Beras Part One') + '. '
        except: pass

        points = wallet.browser.get_points_amount()

        if completed == 7:
            return f'✅ Total points: {points}. Completed {completed}/7 quests'
        else:
            return f'Total points: {points}. Completed {completed}/7 quests'



def run_accs(accs_data: list):
    funcs_dct = {
        'Onchain actions': berachain_onchain,
        'Claim quests': galxe_quests_confirm,
    }

    for index, acc in enumerate(accs_data):
        try:
            print('')
            sleep(0.1)

            windowname.update_accs()
            browser = Browser()
            tg_report = TgReport()
            wallet = Wallet(privatekey=acc['privatekey'], tg_report=tg_report, browser=browser)
            email = Rambler(mail_data=acc['mail_data'])

            logger.info(f'[•] START | [{windowname.accs_done}/{windowname.accs_amount}] {wallet.address}')

            wallet.status = funcs_dct[MODE](wallet=wallet, email=email)

        except Exception as err:
            wallet.status = '❌ ' + str(err)
            logger.error(str(err))

        finally:
            excel.edit_table(wallet=wallet)
            tg_report.send_log(wallet=wallet, window_name=windowname)
            sleeping(SLEEP_BETWEEN_ACCS[0], SLEEP_BETWEEN_ACCS[1]) # задержка между аккаунтами


if __name__ == '__main__':
    if not os.path.isdir('results'): os.mkdir('results')
    with open('privatekeys.txt') as f: p_keys = f.read().splitlines()
    with open('emails.txt') as f: mails_data = f.read().splitlines()

    show_settings()

    MODE = choose_mode()
    if MODE == 'Claim quests' and len(mails_data) != 0:
        if len(p_keys) != len(mails_data):
            raise Exception(f'Private keys amount must be equals emails! {len(p_keys)} != {len(mails_data)}. Or remove all emails from .txt')
        accs_data = [{'privatekey': pk, 'mail_data': mail_data} for pk, mail_data in zip(p_keys, mails_data)]
    else:
        accs_data = [{'privatekey': pk, 'mail_data': None} for pk in p_keys]

    excel = Excel(total_len=len(p_keys))
    windowname = WindowName(len(p_keys))
    if SHUFFLE_WALLETS: shuffle(accs_data)

    try:
        run_accs(accs_data=accs_data)
    except Exception as err:
        logger.error(f'Global error: {err}')

    logger.success(f'All accs done.\n\n')
    sleep(0.1)
    input(' > Exit')
