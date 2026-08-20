import sys
import time
import pandas as pd
import glob
import json
from cpp_quant import CppQuant

print("="*70)
print("🚀 БОДИТ КОМИСС/SPREAD ТООЦООЛОЛ БҮХИЙ БЭКТЕСТ")
print("="*70)

# 1. Өгөгдөл
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
print(f"✅ {len(df):,} мөрийг {time.time()-start_load:.2f} секундэд бэлдлээ")

# 2. Бэктест хийх функц (комисс/spread-тэй)
def run_backtest_with_cost(df, short=20, long=50, commission=0.001, spread=0.0005):
    """
    SMA crossover бэктест + комисс/spread
    """
    # SMA тооцоолох
    df['SMA_short'] = df['close'].rolling(short).mean()
    df['SMA_long'] = df['close'].rolling(long).mean()
    
    # Дохио
    df['signal'] = 0
    df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1
    df.loc[df['SMA_short'] <= df['SMA_long'], 'signal'] = -1
    df['position'] = df['signal'].diff()
    
    # Арилжаа хийх
    capital = 10000.0
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(1, len(df)):
        price = df['close'].iloc[i]
        
        if df['position'].iloc[i] == 2:  # BUY
            if position == 0:
                # 🔥 Комисс/spread-ийг харгалзах
                entry_price = price * (1 + commission + spread)  # Худалдан авах үнэ
                position = 1
        elif df['position'].iloc[i] == -2:  # SELL
            if position == 1:
                # 🔥 Комисс/spread-ийг харгалзах
                exit_price = price * (1 - commission - spread)  # Худалдах үнэ
                pnl = (exit_price - entry_price) / entry_price
                trades.append(pnl)
                position = 0
                capital *= (1 + pnl)
    
    # Хаагдаагүй позиц
    if position == 1:
        exit_price = df['close'].iloc[-1] * (1 - commission - spread)
        pnl = (exit_price - entry_price) / entry_price
        trades.append(pnl)
        capital *= (1 + pnl)
    
    # Статистик
    if trades:
        winrate = sum(1 for t in trades if t > 0) / len(trades) * 100
        total_return = (capital / 10000.0) - 1
        avg_pnl = sum(trades) / len(trades)
        std_pnl = (sum((t - avg_pnl)**2 for t in trades) / len(trades)) ** 0.5
        sharpe = (avg_pnl / std_pnl) * (252 * 6.5 * 12) ** 0.5 if std_pnl > 0 else 0
    else:
        winrate = 0
        total_return = 0
        sharpe = 0
    
    return {
        'trades': len(trades),
        'winrate': winrate,
        'total_return': total_return,
        'sharpe': sharpe,
        'capital': capital
    }

# 3. Sweep (комисс/spread-тэй)
timeframes = [5, 15, 30, 60]
commissions = [0.0005, 0.001, 0.0015, 0.002]
spreads = [0.0003, 0.0005, 0.0008]  # XAUUSD spread
results = []
sweep_start = time.time()

for h in timeframes:
    df_resampled = df.resample(f'{h}min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    print(f"\n⏳ {h}min агрегацлаж байна... ({len(df_resampled):,} candle)")
    
    for c in commissions:
        for s in spreads:
            # Комисс/spread-тэй бэктест
            result = run_backtest_with_cost(df_resampled, 20, 50, c, s)
            
            results.append({
                'timeframe': f'{h}min',
                'commission': c,
                'spread': s,
                'trades': result['trades'],
                'winrate': result['winrate'],
                'return': result['total_return'] * 100,
                'sharpe': result['sharpe'],
                'final_capital': result['capital']
            })
            
            print(f"  h={h:2d}min, c={c*100:.2f}%, s={s*100:.2f}% | Winrate: {result['winrate']:.2f}%, Trades: {result['trades']}")

sweep_time = time.time() - sweep_start
print(f"\n✅ Нийт Sweep хугацаа: {sweep_time:.2f} секунд")

# 4. Хадгалах
output_file = 'data/curated/xauusd/backtest_with_cost.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"📊 Үр дүн хадгалагдлаа: {output_file}")

# 5. Шилдэг хувилбар (хамгийн өндөр Sharpe)
if results:
    best = max(results, key=lambda x: x['sharpe'])
    print(f"\n🏆 ХАМГИЙН САЙН:")
    print(f"  Цаг.хүрээ: {best['timeframe']}")
    print(f"  Комисс: {best['commission']*100:.2f}%")
    print(f"  Spread: {best['spread']*100:.2f}%")
    print(f"  Winrate: {best['winrate']:.2f}%")
    print(f"  Sharpe: {best['sharpe']:.2f}")
    print(f"  Эцсийн капитал: ${best['final_capital']:.2f}")

print("\n" + "="*70)
print("✅ БҮХ АЖИЛ ДУУССАН!")
