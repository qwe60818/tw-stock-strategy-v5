#!/usr/bin/env python3
"""
台股短線策略 v5.0 - 回測系統（75檔）
"""

import requests
from datetime import datetime, timedelta

url = 'https://api.finmindtrade.com/api/v4/data'
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMy0xMCAwMjowODoyMyIsInVzZXJfaWQiOiJxd2U2MDgxOCIsImVtYWlsIjoicXdlNjA4MThAaG90bWFpbC5jb20iLCJpcCI6IjEyMy4xOTQuMTg4LjEyOSJ9.qXBUvBVraRHJf4O4ANWerVEvqgTrw9uAHffUX7hphDQ'

# 75檔
stocks = [
    # 電子權值股（25檔）
    '2330', '2317', '2454', '2308', '2379', '3034', '2382', '2377', '2458', '3035',
    '3008', '2409', '2478', '2345', '2393', '2401', '2448', '3231', '3702', '3711',
    '6415', '6449', '6456', '6515', '6550',
    # 電子中小股（17檔）
    '2362', '2376', '2385', '2429', '2441', '2443', '2451', '2453', '2455',
    '2474', '2481', '2492', '3019', '3021', '3044', '3054', '3094',
    # 傳產（8檔）
    '2618', '2609', '2812', '2855', '2915', '3045', '4904', '6005',
    # 金融（5檔）
    '2881', '2882', '2891', '2892', '5871',
    # 獨立項目（20檔）
    '2344', '2371', '2427', '2431', '2445', '2457', '2486', '3014', '3016', '3022',
    '3037', '3095', '3107', '3141', '3149', '3162', '3189', '3202', '3209', '6625'
]

def get_data(stock_id, start_date, end_date):
    params = {'dataset': 'TaiwanStockPrice', 'data_id': stock_id, 'start_date': start_date, 'end_date': end_date, 'token': token}
    r = requests.get(url, params=params, timeout=30)
    data = r.json().get('data', [])
    if len(data) < 30:
        return None
    import pandas as pd
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    for col in ['close', 'max', 'min', 'Trading_Volume']:
        df[col] = df[col].astype(float)
    return df

def backtest(start_date, end_date, period_name):
    print(f"\n{'='*50}")
    print(f"=== {period_name} 回測 ===")
    print('='*50)
    
    all_trades = []
    stock_stats = {}
    
    for sid in stocks:
        df = get_data(sid, start_date, end_date)
        if df is None:
            continue
        
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA60'] = df['close'].rolling(60).mean()
        df['MA5_Vol'] = df['Trading_Volume'].rolling(5).mean()
        df.dropna(inplace=True)
        
        trades = []
        for i in range(1, len(df)-10):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            ma_bull = row['close'] > row['MA20'] > row['MA60']
            ma20_up = row['MA20'] > prev['MA20']
            vol_break = row['Trading_Volume'] > row['MA5_Vol'] * 1.2
            
            if ma_bull and ma20_up and vol_break:
                entry = row['close']
                
                for j in range(i+1, min(i+11, len(df))):
                    exit_price = df['close'].iloc[j]
                    ret = (exit_price - entry) / entry
                    
                    if ret >= 0.08:
                        trades.append({'ret': ret, 'reason': '停利+8%'})
                        break
                    elif ret <= -0.05:
                        trades.append({'ret': ret, 'reason': '停損-5%'})
                        break
                    elif j == i+10:
                        trades.append({'ret': ret, 'reason': '時間出口'})
                        break
        
        if trades:
            wins = sum(1 for t in trades if t['ret'] > 0)
            total_ret = sum(t['ret'] for t in trades)
            stock_stats[sid] = {'trades': len(trades), 'wins': wins, 'win_rate': wins/len(trades), 'total_ret': total_ret}
            all_trades.extend(trades)
    
    print(f"\n{'股票':<6} {'交易數':>6} {'勝率':>8} {'報酬':>10}")
    print('-'*35)
    for sid, stat in sorted(stock_stats.items(), key=lambda x: x[1]['total_ret'], reverse=True):
        print(f"{sid:<6} {stat['trades']:>6} {stat['win_rate']:>7.0%} {stat['total_ret']:>+9.1%}")
    
    if all_trades:
        total_wins = sum(1 for t in all_trades if t['ret'] > 0)
        total_ret = sum(t['ret'] for t in all_trades)
        print('-'*35)
        print(f"{'總計':<6} {len(all_trades):>6} {total_wins/len(all_trades):>7.0%} {total_ret:>+9.1%}")
    else:
        print('\n無交易訊號')

if __name__ == "__main__":
    print("\n" + "="*60)
    print("       台股短線策略 v5.0 回測系統（75檔）")
    print("="*60)
    
    backtest("2025-01-01", "2026-03-09", "2025/1 現在")
    backtest("2026-01-01", "2026-03-09", "2026/1 現在")
    
    print("\n回測完成!")
