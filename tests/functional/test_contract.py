import pytest
from ape import Contract
from ape.exceptions import ContractLogicError, OutOfGasError

from ape_starknet.exceptions import StarknetEcosystemError


def test_is_token(contract, tokens):
    assert not tokens.is_token(contract.address)


def test_declare_then_deploy(account, chain, project, provider, factory_contract_container):
    # Declare contract type. The result should contain a 'class_hash'.
    declaration = account.declare(project.MyContract)
    assert declaration.class_hash

    # Ensure can use class_hash in factory contract
    factory = factory_contract_container.deploy(declaration.class_hash)
    receipt = factory.create_my_contract(sender=account)
    logs = list(receipt.decode_logs(factory.contract_deployed))
    new_contract_address = provider.starknet.decode_address(logs[0]["contract_address"])

    # Ensure can interact with deployed contract from 'class_hash'.
    new_contract_instance = Contract(
        new_contract_address, contract_type=project.MyContract.contract_type
    )
    assert new_contract_instance
    new_contract_instance.initialize(sender=account)
    balance_pre_call = new_contract_instance.get_balance(account)
    new_contract_instance.increase_balance(account, 9, sender=account)
    assert new_contract_instance.get_balance(account) == balance_pre_call + 9


def test_get_caller_address(contract, account, provider):
    expected = provider.starknet.encode_address(account.address)
    assert contract.get_caller(sender=account).return_value == expected


def test_validate_signature_on_chain(contract, account, initial_balance):
    # NOTE: This test validates the account signature but the transaction
    # is not directly sent from the account.
    increase_amount = 42 * 2**152

    signature = account.sign_message(increase_amount)
    contract.increase_balance_signed(
        account.public_key, account.address, increase_amount, signature, sender=account
    )

    actual = contract.get_balance(account)
    expected = initial_balance + increase_amount
    assert actual == expected


def test_transact_from_account(contract, account, initial_balance):
    increase_amount = 123456
    receipt = contract.increase_balance(account, increase_amount, sender=account)
    actual_from_receipt = receipt.return_value
    actual_from_call = contract.get_balance(account)
    expected = initial_balance + increase_amount
    assert actual_from_receipt == actual_from_call == expected


def test_contracts_as_arguments(contract, account):
    initial_balance = contract.get_balance(contract)
    increase_amount = 123456
    receipt = contract.increase_balance(contract, increase_amount, sender=account)
    actual_from_receipt = receipt.return_value
    actual_from_call = contract.get_balance(contract)
    expected = initial_balance + increase_amount
    assert actual_from_receipt == actual_from_call == expected


def test_unsigned_contract_transaction(contract, account, initial_balance):
    increase_amount = 123456

    with pytest.raises(
        StarknetEcosystemError, match="'sender=<account>' required for invoke transactions"
    ):
        contract.increase_balance(account.address, increase_amount)


def test_decode_logs(contract, account, ecosystem):
    increase_amount = 9933
    receipt = contract.increase_balance(account.address, increase_amount, sender=account)
    logs = list(receipt.decode_logs(contract.balance_increased))
    assert len(logs) == 1
    assert logs[0].amount == increase_amount

    from_address = receipt.logs[0]["from_address"]
    log_sender_address = ecosystem.decode_address(from_address)
    assert log_sender_address == contract.address


def test_revert_message(contract, account):
    reason = "Already initialized"
    with pytest.raises(ContractLogicError, match=reason):
        # Already initialized from fixture
        contract.initialize(sender=account)


def test_revert_no_message(contract, account):
    contract.reset(sender=account)
    reason = "An ASSERT_EQ instruction failed.*"
    with pytest.raises(ContractLogicError, match=reason):
        contract.increase_balance(account.address, 123, sender=account)

    # Re-initialize (re-store state)
    contract.initialize(sender=account)


def test_unable_to_afford_transaction(contract, account, provider):
    with pytest.raises(OutOfGasError):
        contract.increase_balance(account.address, 1, sender=account, max_fee=1)


def test_array_inputs(contract, account):
    # This test makes sure we can pass python lists as arguments
    # to Cairo methods that accept arrays.
    # NOTE: Due to a limitation in ape, we have to include the array length argument.
    contract.store_sum(3, [1, 2, 3], sender=account)
    assert contract.get_last_sum() == 6


def test_complex_struct_argument(contract, account):
    complex_struct = {
        "timestamp": 42,
        "value0": 123,  # == Uint256(123, 0)
        "value1": {
            "low": 0,
            "high": 123,
        },  # == Uint256(0, 123) == 41854731131275431005995076714107490009088
    }
    receipt = contract.store_complex_struct(complex_struct, sender=account)
    assert receipt.return_value == {
        "timestamp": 42,
        "value0": 123,
        "value1": 41854731131275431005995076714107490009088,
    }


#
# Test external, and view, methods
#


@pytest.mark.parametrize(
    "method, returndata_expected, return_value_expected",
    [
        ("array", ["0x3", "0x1", "0x2", "0x3"], [1, 2, 3]),
        (
            "array_complex_struct",
            [
                "0x3",
                "0x0",
                "0x7b",
                "0x0",
                "0x0",
                "0x7b",
                "0x1",
                "0x0",
                "0x7b",
                "0x7b",
                "0x0",
                "0x2",
                "0x0",
                "0x0",
                "0x0",
                "0x0",
            ],
            [
                {
                    "timestamp": 0,
                    "value0": 123,
                    "value1": 41854731131275431005995076714107490009088,
                },
                {
                    "timestamp": 1,
                    "value0": 41854731131275431005995076714107490009088,
                    "value1": 123,
                },
                {"timestamp": 2, "value0": 0, "value1": 0},
            ],
        ),
        (
            "array_uint256",
            ["0x3", "0x7b", "0x0", "0x0", "0x7b", "0x0", "0x0"],
            [
                123,
                41854731131275431005995076714107490009088,
                0,
            ],
        ),
        (
            "complex_struct",
            ["0x4d2", "0x7b", "0x0", "0x0", "0x7b"],
            {
                "timestamp": 1234,
                "value0": 123,
                "value1": 41854731131275431005995076714107490009088,
            },
        ),
        ("felt", ["0x2"], 2),
        (
            "mix",
            [
                "0x1",
                "0x2",
                "0x3",
                "0x4",
                "0x7b",
                "0x0",
                "0x3",
                "0x8",
                "0x9",
                "0xa",
                "0xb",
                "0x0",
                "0x7b",
            ],
            (
                1,
                [3, 4],
                123,
                [8, 9, 10],
                11,
                41854731131275431005995076714107490009088,
            ),
        ),
        ("uint256", ["0x1", "0x0"], 1),
        (
            "uint256s",
            ["0x7b", "0x0", "0x0", "0x7b", "0x0", "0x0"],
            (
                123,
                41854731131275431005995076714107490009088,
                0,
            ),
        ),
    ],
)
def test_external_and_view_method_outputs(
    method, returndata_expected, return_value_expected, contract, account
):
    # Check the view method
    return_value = getattr(contract, f"{method}_view")()
    assert return_value == return_value_expected

    # Check the external method
    receipt = getattr(contract, f"{method}_external")(sender=account)
    assert receipt.returndata == returndata_expected
    assert receipt.return_value == return_value


def test_estimate_gas_cost_external_method(contract, account, provider):
    estimated_fee = contract.increase_balance.estimate_gas_cost(account.address, 1, sender=account)
    assert estimated_fee > 100_000_000_000_000

    receipt = contract.increase_balance(account.address, 1, sender=account)
    assert receipt.gas_used == estimated_fee
    assert receipt.max_fee > estimated_fee
    assert receipt.total_fees_paid == receipt.gas_used
    assert not receipt.ran_out_of_gas
    assert provider.gas_price >= 100_000_000_000


def test_estimate_gas_cost_view_method(contract, account, provider):
    estimated_fee = contract.get_balance.estimate_gas_cost(account.address, sender=account)
    assert estimated_fee > 100_000_000_000_000
    assert provider.gas_price >= 100_000_000_000


def test_estimate_gas_cost_view_method_2(contract, account):
    estimated_fee = contract.get_balance.estimate_gas_cost(account, sender=account)
    assert estimated_fee > 100_000_000_000_000


def test_token_event(token_contract, account, contract):

    receipt = contract.fireTokenEvent(token_contract.address, sender=account)
    print(receipt)

    print("contract event")
    logs_contract_events = list(receipt.decode_logs(contract.TokenEvent))
    print(logs_contract_events)

    print("token event")
    logs_transfer = list(receipt.decode_logs(token_contract.Transfer))
    print(logs_transfer)

    logs_mint = list(receipt.decode_logs(token_contract.Mint))
    print(logs_mint)
