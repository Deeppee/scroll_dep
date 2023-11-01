import json
import sys
import random
import string
import time
from web3 import Web3
from solcx import compile_source, set_solc_version, install_solc
from settings import rpc_scroll, rpc_eth, gwei, time_to_sleep, min_time, max_time

w3 = Web3(Web3.HTTPProvider(rpc_scroll))
w3_eth = Web3(Web3.HTTPProvider(rpc_eth))

link = "https://scrollscan.com/tx/"

def compiler(contract_name, message):
    install_solc('0.8.2')
    set_solc_version('0.8.2')

    contract_source_code = '''
    contract {} {{
        string public message = "{}";
    }}
    '''.format(contract_name, message)

    def compile_contract(source_code):
        compiled_sol = compile_source(source_code)
        contract_interface = compiled_sol[f'<stdin>:{contract_name}']
        return contract_interface

    contract_interface = compile_contract(contract_source_code)
    abi = contract_interface['abi']
    bytecode = contract_interface['bin']
    return abi, bytecode


def random_string(length=10):
    characters = string.ascii_letters
    return ''.join(random.choice(characters) for i in range(length - 1))


def gas_price_checker():
    while True:
        gas_price = w3_eth.eth.gas_price
        gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
        if gas_price_gwei > gwei:
            print(f"Gas price is too high: {round(gas_price_gwei, 2)}, have to sleep {time_to_sleep} sec")
            time.sleep(time_to_sleep)
        else:
            print(f"Gas price is good: {round(gas_price_gwei, 2)}")
            return


def total_wallets():
    with open("pks.txt", 'r') as file:
        content = file.readlines()
        line_count = len(content)
        return line_count


with open("pks.txt", "r") as f:
    total_wallets = total_wallets()
    counter = 0
    for k in f:
        counter += 1
        private_key = k.strip()
        wallet_address = w3.eth.account.from_key(private_key).address
        print(f'Wallet {counter}/{total_wallets} ||| {wallet_address}')
        gas_price_checker()
        print("Deploying contract...")

        nonce = w3.eth.get_transaction_count(wallet_address)
        contract_name = random_string()
        message = random_string()
        result = compiler(contract_name, message)
        abi = result[0]
        bytecode = result[1]
        contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        transaction = contract.constructor().build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 250000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        try:
            signed_transaction = w3.eth.account.sign_transaction(transaction, private_key)
            transaction_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
            transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
        except Exception as e:
            print(f"Something went wrong ||| ERROR: {e}")
            continue

        print(f"Contract Deployed At: {transaction_receipt['contractAddress']}")
        print(f"Tx hash: {link}{transaction_hash.hex()}")

        tt = random.randint(min_time, max_time)
        print(f'Next address in: {tt} sec')
        time.sleep(tt)

