import sys
import time
import pandas as pd
import numpy as np
import glob
import json

print("="*70)
print("💰 БОДИТ КОМИСС/SPREAD-ТЭЙ БЭКТЕСТ (Python векторчилсон)")
print("="*70)

# 1. Өгөгдөл ачаалах
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

# 2. Бэктест функц (векторчилсон, комисс/spread-тэй)
def backtest_sma_vectorized(df, short=20, long=50, commission=0.001, spread=0.0005):
    """
    SMA crossover бэктест – бүрэн векторчилсон (циклгүй)
    Комисс/spread-ийг арилжаа бүрт тооцно
    """
    # SMA тооцоолох
    sma_short = df['close'].rolling(short).mean()
    sma_long = df['close'].rolling(long).mean()
    
    # Дохио: 1 (BUY), -1 (SELL), 0 (HOLD)
    signal = np.zeros(len(df))
    signal[(sma_short > sma_long) & (sma_short.shift(1) <= sma_long.shift(1))] = 1
    signal[(sma_short < sma_long) & (sma_short.shift(1) >= sma_long.shift(1))] = -1
    
    # Арилжааны цэгүүд
    trades = []
    position = 0
    entry_price = 0
    capital = 10000.0
    
    for i in range(1, len(df)):
        if signal[i] == 1 and position == 0:
            # BUY – комисс/spread-ийг нэмэх
            entry_price = df['close'].iloc[i] * (1 + commission + spread)
            position = 1
        elif signal[i] == -1 and position == 1:
            # SELL – комисс/spread-ийг хасах
            exit_price = df['close'].iloc[i] * (1 - commission - spread)
            pnl = (exit_price - entry_price) / entry_price
            trades.append(pnl)
            capital *= (1 + pnl)
            position = 0
    
    # Сүүлийн позиц хаах
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
    
    return {
        'trades': len(trades),
        'winrate': winrate,
        'total_return': total_return * 100,
        'sharpe': sharpe,
        'final_capital': capital,
        'avg_pnl': avg_pnl if trades else 0
    }

# 3. Sweep (бүх цагийн хүрээ, стратеги, комисс)
timeframes = [5, 15, 30, 60]
strategies = [
    ('SMA_10_30', 10, 30),
    ('SMA_20_50', 20, 50),
]
commissions = [0.0005, 0.001, 0.0015]  # 0.05%, 0.10%, 0.15%
spread = 0.0005  # XAUUSD-ийн ойролцоо spread

all_results = []
sweep_start = time.time()

for h in timeframes:
    print(f"\n⏳ {h}min агрегацлаж байна...")
    df_h = df.resample(f'{h}min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    print(f"   {len(df_h):,} candle")

    for name, short, long in strategies:
        for c in commissions:
            result = backtest_sma_vectorized(df_h, short, long, c, spread)
            result.update({
                'timeframe': f'{h}min',
                'strategy': name,
                'commission': c,
                'spread': spread
            })
            all_results.append(result)
            
            print(f"   {name} | c={c*100:.2f}% | Winrate: {result['winrate']:.2f}%, Trades: {result['trades']}, Return: {result['total_return']:.2f}%")

sweep_time = time.time() - sweep_start
print(f"\n✅ Нийт хугацаа: {sweep_time:.2f} сек")

# 4. Шилдэг (комисс/spread-тэй)
if all_results:
    best = max(all_results, key=lambda x: x['winrate'])
    print("\n" + "="*70)
    print("🏆 ХАМГИЙН САЙН (Комисс/Spread-тэй):")
    print(f"  Стратеги: {best['strategy']}")
    print(f"  Цаг.хүрээ: {best['timeframe']}")
    print(f"  Комисс: {best['commission']*100:.2f}%")
    print(f"  Spread: {best['spread']*100:.2f}%")
    print(f"  Winrate: {best['winrate']:.2f}%")
    print(f"  Trades: {best['trades']}")
    print(f"  Return: {best['total_return']:.2f}%")
    print(f"  Sharpe: {best['sharpe']:.2f}")
    print(f"  Final Capital: ${best['final_capital']:.2f}")

# 5. Харьцуулалт (комиссгүй vs комисстэй)
print("\n" + "="*70)
print("📊 КОМИССЫН НӨЛӨӨ (60min, SMA_20_50):")
base = [r for r in all_results if r['timeframe'] == '60min' and r['strategy'] == 'SMA_20_50']
if base:
    no_commission = [r for r in base if r['commission'] == 0.0005][0]
    high_commission = [r for r in base if r['commission'] == 0.0015][0]
    print(f"  Комисс 0.05%: Winrate {no_commission['winrate']:.2f}%, Return {no_commission['total_return']:.2f}%")
    print(f"  Комисс 0.15%: Winrate {high_commission['winrate']:.2f}%, Return {high_commission['total_return']:.2f}%")
    print(f"  Зөрүү: Winrate {no_commission['winrate'] - high_commission['winrate']:.2f}%")

# 6. Хадгалах
with open('commission_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print("\n📊 Үр дүн хадгалагдлаа: commission_results.json")
print("="*70)
print("✅ БҮХ АЖИЛ ДУУССАН!")
