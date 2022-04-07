def fee_too_high(order_preset, contract, ib_conn, fee_limit):
    test_order=order_preset(orderType='MKT',whatIf=True)
    test_trade=ib_conn.whatIfOrder(contract, test_order)
    if type(test_trade)==list:
        return(False)
    else:
        if test_trade.maxCommission>fee_limit:
            print("PASS:", contract.symbol, "at", test_trade.maxCommission)
            return True
        else:
            print("FAIL:", contract.symbol, "at", test_trade.maxCommission)
            return False
