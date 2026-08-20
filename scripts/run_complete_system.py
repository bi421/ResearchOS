"""
ResearchOS Complete System – Бүх стратеги, бүх цагийн хүрээ, бодит комисс/spread
"""
import sys
import time
import pandas as pd
import glob
import json
from datetime import datetime

print("="*70)
print("🚀 RESEARCHOS COMPLETE SYSTEM – БҮХ СТРАТЕГИ + БОДИТ КОМИСС")
print("="*70)

# ============================================================
# 1. ӨГӨГДӨЛ АЧААЛАХ (ХУРДАН)
# ============================================================
start_load = time.time()
files = glob.glob('data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv')
if not files:
    print("❌ Өгөгдөл олдсонгүй!")
    sys.exit(1)

df = pd.concat([
    pd.read_csv(f, sep=';', header=None, 
                names=['datetime','open','high','low','close','volume'],
                dtype={'datetime': str})
    for f in files
], ignore_index=True)

df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
df = df.set_index('datetime')
print(f"✅ {len(df):,} мөрийг {time.time()-start_load:.2f} сек")

# ============================================================
# 2. БЭКТЕСТ ФУНКЦ (КОМИСС/SPREAD-ТЭЙ)
# ============================================================
def backtest_sma(df, short=10, long=30, commission=0.001, spread=0.0005):
    """SMA crossover + бодит комисс/spread"""
    df = df.copy()
    df['SMA_short'] = df['close'].rolling(short).mean()
    df['SMA_long'] = df['close'].rolling(long).mean()
    df['signal'] = 0
    df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1
    df.loc[df['SMA_short'] <= df['SMA_long'], 'signal'] = -1
    df['position'] = df['signal'].diff()
    
    capital = 10000.0
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(1, len(df)):
        price = df['close'].iloc[i]
        if df['position'].iloc[i] == 2 and position == 0:
            entry_price = price * (1 + commission + spread)
            position = 1
        elif df['position'].iloc[i] == -2 and position == 1:
            exit_price = price * (1 - commission - spread)
            pnl = (exit_price - entry_price) / entry_price
            trades.append(pnl)
            capital *= (1 + pnl)
            position = 0
    
    if position == 1:
        exit_price = df['close'].iloc[-1] * (1 - commission - spread)
        pnl = (exit_price - entry_price) / entry_price
        trades.append(pnl)
        capital *= (1 + pnl)
    
    if trades:
        winrate = sum(1 for t in trades if t > 0) / len(trades) * 100
        total_return = (capital / 10000.0) - 1
        avg_pnl = sum(trades) / len(trades)
        std_pnl = (sum((t - avg_pnl)**2 for t in trades) / len(trades)) ** 0.5
        sharpe = (avg_pnl / std_pnl) * (252 * 6.5 * 12) ** 0.5 if std_pnl > 0 else 0
    else:
        winrate, total_return, sharpe = 0, 0, 0
    
    return {'trades': len(trades), 'winrate': winrate, 'return': total_return * 100, 'sharpe': sharpe, 'capital': capital}

def backtest_rsi(df, period=14, oversold=30, overbought=70, commission=0.001, spread=0.0005):
    """RSI стратеги + комисс/spread"""
    df = df.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['signal'] = 0
    df.loc[df['RSI'] < oversold, 'signal'] = 1
    df.loc[df['RSI'] > overbought, 'signal'] = -1
    df['position'] = df['signal'].diff()
    
    capital = 10000.0
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(1, len(df)):
        price = df['close'].iloc[i]
        if df['position'].iloc[i] == 2 and position == 0:
            entry_price = price * (1 + commission + spread)
            position = 1
        elif df['position'].iloc[i] == -2 and position == 1:
            exit_price = price * (1 - commission - spread)
            pnl = (exit_price - entry_price) / entry_price
            trades.append(pnl)
            capital *= (1 + pnl)
            position = 0
    
    if position == 1:
        exit_price = df['close'].iloc[-1] * (1 - commission - spread)
        pnl = (exit_price - entry_price) / entry_price
        trades.append(pnl)
        capital *= (1 + pnl)
    
    if trades:
        winrate = sum(1 for t in trades if t > 0) / len(trades) * 100
        total_return = (capital / 10000.0) - 1
        avg_pnl = sum(trades) / len(trades)
        std_pnl = (sum((t - avg_pnl)**2 for t in trades) / len(trades)) ** 0.5
        sharpe = (avg_pnl / std_pnl) * (252 * 6.5 * 12) ** 0.5 if std_pnl > 0 else 0
    else:
        winrate, total_return, sharpe = 0, 0, 0
    
    return {'trades': len(trades), 'winrate': winrate, 'return': total_return * 100, 'sharpe': sharpe, 'capital': capital}

# ============================================================
# 3. БҮХ СТРАТЕГИ × БҮХ ЦАГИЙН ХҮРЭЭ
# ============================================================
timeframes = [5, 15, 30, 60]
strategies = [
    ('SMA_10_30', lambda d: backtest_sma(d, 10, 30)),
    ('SMA_20_50', lambda d: backtest_sma(d, 20, 50)),
    ('RSI_14', lambda d: backtest_rsi(d, 14, 30, 70)),
]
commissions = [0.0005, 0.001, 0.0015]
spread = 0.0005

all_results = []
sweep_start = time.time()

for h in timeframes:
    df_h = df.resample(f'{h}min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    print(f"\n⏳ {h}min ({len(df_h):,} candle)")
    
    for name, strategy in strategies:
        for c in commissions:
            result = strategy(df_h)
            result.update({
                'timeframe': f'{h}min',
                'strategy': name,
                'commission': c,
                'spread': spread
            })
            all_results.append(result)
            print(f"  {name}: c={c*100:.2f}% | Winrate: {result['winrate']:.2f}%, Trades: {result['trades']}")

sweep_time = time.time() - sweep_start
print(f"\n✅ Нийт хугацаа: {sweep_time:.2f} сек")

# ============================================================
# 4. ШИЛДЭГ СТРАТЕГИ
# ============================================================
if all_results:
    best = max(all_results, key=lambda x: x['winrate'])
    print("\n" + "="*70)
    print("🏆 ХАМГИЙН САЙН СТРАТЕГИ:")
    print(f"  Стратеги: {best['strategy']}")
    print(f"  Цаг.хүрээ: {best['timeframe']}")
    print(f"  Комисс: {best['commission']*100:.2f}%")
    print(f"  Winrate: {best['winrate']:.2f}%")
    print(f"  Trades: {best['trades']}")
    print(f"  Return: {best['return']:.2f}%")
    print(f"  Sharpe: {best['sharpe']:.2f}")
    print(f"  Final Capital: ${best['capital']:.2f}")

# ============================================================
# 5. ТАЙЛАН ХАДГАЛАХ
# ============================================================
output = {
    'timestamp': datetime.now().isoformat(),
    'data_points': len(df),
    'results': all_results,
    'best': best
}
with open('complete_system_report.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n📊 Тайлан хадгалагдлаа: complete_system_report.json")
print("="*70)
print("✅ БҮХ АЖИЛ ДУУССАН!")
