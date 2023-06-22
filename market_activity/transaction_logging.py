import datetime 

def log_trade(trade,trade_reason,log_dir,notes={}):
    traded=len(trade.fills)>0
    to_log={'symbol':trade.contract.localSymbol,
            'date':datetime.datetime.now().date().__str__(),
            'order_id':trade.order.permId,
            'action':trade.order.action,
            'quantity':sum([fill.execution.shares for fill in trade.fills]) if traded else trade.order.totalQuantity,
            'order_type':trade.order.orderType,
            'lmt_price':trade.order.lmtPrice,
            'tif':trade.order.tif,
            'status':trade.orderStatus.status,
            'fills':len(trade.fills),
            'price_paid':trade.fills[0].execution.price if traded else 0,
            'commission':sum([fill.commissionReport.commission for fill in trade.fills]),
            'realizedPNL':sum([fill.commissionReport.realizedPNL for fill in trade.fills]),
            'trade_reason':trade_reason,
            'record_ts':datetime.datetime.now().timestamp(),
            'first_fill_ts':min([fill.time for fill in trade.fills]).timestamp() if traded else 0
            }
    to_log.update(notes)
    with open(log_dir, 'a') as log_file:
        log_file.write(to_log.__str__()+"\n")

