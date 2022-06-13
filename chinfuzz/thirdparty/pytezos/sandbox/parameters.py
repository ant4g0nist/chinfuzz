from typing import Any, Dict

from pytezos.crypto.key import Key

EDO = 'PtEdo2ZkT9oKpimTah6x2embF25oss54njMuPzkJTEi5RqfdZFA'
FLORENCE = 'PsFLorenaUUuikDWvMDr6fGBRG8kt3e3D3fHoXK1j1BFRxeSH4i'
GRANADA = 'PtGRANADsDU8R9daYKAgWnQYAJ64omN1o3KMGVCykShA97vQbvV'
HANGZHOU = 'PtHangz2aRngywmSRGGvrcTyMbbdpWdpFKuS4uMWxg2RaH9i1qx'
ITHACA = 'Psithaca2MLRFYargivpo7YvUr7wUDqyxrdhC5CQq78mRvimz6A'
LATEST = ITHACA

protocol_version = {EDO: 8, FLORENCE: 9, GRANADA: 10, HANGZHOU: 11, ITHACA: 12}

sandbox_commitment = {
    "mnemonic": [
        "arctic",
        "blame",
        "brush",
        "economy",
        "solar",
        "swallow",
        "canvas",
        "live",
        "vote",
        "two",
        "post",
        "neutral",
        "spare",
        "split",
        "fall",
    ],
    "activation_code": "7375ef222cc038001b6c8fb768246c86e994745b",
    "amount": "38323962971",
    "pkh": "tz1W86h1XuWy6awbNUTRUgs6nk8q5vqXQwgk",
    "password": "ZuPOpZgMNM",
    "email": "nbhcylbg.xllfjgrk@tezos.example.org",
}

sandbox_addresses = {
    'activator': 'tz1TGu6TN5GSez2ndXXeDX6LgUDvLzPLqgYV',
    'bootstrap5': 'tz1ddb9NMYHZi5UzPdzTZMYQQZoMub195zgv',
    'bootstrap4': 'tz1b7tUupMgCNw2cCLpKTkSD1NZzB5TkP2sv',
    'bootstrap3': 'tz1faswCTDciRzE4oJ9jn2Vm2dvjeyA9fUzU',
    'bootstrap2': 'tz1gjaF81ZRRvdzjobyfVNsAeSC6PScjfQwN',
    'bootstrap1': 'tz1KqTpEZ7Yob7QbPE4Hy4Wo8fHG8LhKxZSx',
}

sandbox_params: Dict[str, Any] = {
    'bootstrap_accounts': [
        ['edpkuBknW28nW72KG6RoHtYW7p12T6GKc7nAbwYX5m8Wd9sDVC9yav', '4000000000000'],
        ['edpktzNbDAUjUk697W7gYg2CRuBQjyPxbEg8dLccYYwKSKvkPvjtV9', '4000000000000'],
        ['edpkuTXkJDGcFd5nh6VvMz8phXxU3Bi7h6hqgywNFi1vZTfQNnS1RV', '4000000000000'],
        ['edpkuFrRoDSEbJYgxRtLx2ps82UdaYc1WwfS9sE11yhauZt5DgCHbU', '4000000000000'],
        ['edpkv8EUUH68jmo3f7Um5PezmfGrRF24gnfLpH3sVNwJnV5bVCxL2n', '4000000000000'],
    ],
    'bootstrap_contracts': [],
    'commitments': [
        [
            Key.from_faucet(sandbox_commitment).blinded_public_key_hash(),
            '100500000000',
        ],
    ],
    'preserved_cycles': 2.0,
    'blocks_per_cycle': 8.0,
    'blocks_per_commitment': 4.0,
    'blocks_per_voting_period': 64.0,
    'hard_gas_limit_per_operation': '1040000',
    'hard_gas_limit_per_block': '10400000',
    'proof_of_work_threshold': str((1 << 63) - 1),
    'tokens_per_roll': '8000000000',
    'seed_nonce_revelation_tip': '125000',
    'origination_size': 257.0,
    'cost_per_byte': '250',
    'hard_storage_limit_per_operation': '60000',
    'quorum_min': 2000.0,
    'quorum_max': 7000.0,
    'min_proposal_quorum': 500.0,
}


def get_protocol_parameters(protocol_hash: str) -> Dict[str, Any]:
    params = sandbox_params.copy()
    if protocol_version[protocol_hash] >= 12:
        params = {
            **params,
            'blocks_per_stake_snapshot': 4.0,
            'consensus_committee_size': 526.0,
            'consensus_threshold': 0.0,
            'baking_reward_fixed_portion': '333333',
            'baking_reward_bonus_per_slot': '3921',
            'endorsing_reward_per_slot': '2604',
            'max_slashing_period': 2.0,
            'frozen_deposits_percentage': 5.0,
            'max_operations_time_to_live': 120.0,
            'delay_increment_per_round': '1',
            'minimal_participation_ratio': {'numerator': 2.0, 'denominator': 3.0},
            'double_baking_punishment': '640000000',
            'ratio_of_frozen_deposits_slashed_per_double_endorsement': {'numerator': 1.0, 'denominator': 2.0},
        }

    if protocol_version[protocol_hash] >= 10:
        params = {
            **params,
            'minimal_block_delay': '1',
            'liquidity_baking_subsidy': '2500000',
            'liquidity_baking_sunset_level': 2032928.0,
            'liquidity_baking_escape_ema_threshold': 1000000.0,
        }

    if protocol_version[protocol_hash] < 10:
        params = {**params, 'test_chain_duration': '1966080'}

    if protocol_version[protocol_hash] < 11:
        params = {
            **params,
            'michelson_maximum_type_size': 1000.0,
        }

    if protocol_version[protocol_hash] < 12:
        params = {
            **params,
            'blocks_per_roll_snapshot': 4.0,
            'time_between_blocks': ['0', '0'],
            'block_security_deposit': '512000000',
            'endorsement_security_deposit': '64000000',
            'baking_reward_per_endorsement': ['1250000', '187500'],
            'endorsement_reward': ['1250000', '833333'],
            'initial_endorsers': 0.0,
            'delay_per_missing_endorsement': '1',
            'endorsers_per_block': 32.0,
        }

    return params
