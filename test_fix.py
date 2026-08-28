import sys
sys.path.insert(0, 'cpp_quant_engine/python')
import cpp_quant_engine as cqe
b = cqe.default_backend()
print('meta', b.meta())
req1 = {'symbol':'BTC','timeframe':'H1','candles':[{'timestamp':'2024-01-01T00:00:00','open':100,'high':101,'low':99,'close':100.5,'volume':1000,'timeframe':'H1'}]}
r = b.backtest_run(req1)
print('WIN no signal', r.final_equity, r.total_bars, r.num_trades)
def my_signal(i,h):
    return {'direction':1,'quantity':1.0}
r = b.backtest_run(req1, signal=my_signal)
print('WIN signal kw', r.final_equity, r.num_trades)
md = b.market_data_load(req1)
print('WIN load', md.size, md.valid)
try:
    b.market_data_load({'symbol':'BTC','timeframe':'H1','candles':[]})
except Exception as e:
    print('empty raises', type(e).__name__, e)
