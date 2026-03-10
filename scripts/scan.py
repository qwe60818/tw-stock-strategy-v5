#!/usr/bin/env python3
"""
台股短線策略 v5.0 - 趨勢突破訊號掃描器
使用 FinMind API
75檔熱門台股
"""

import requests
import sys
from datetime import datetime, timedelta

url = 'https://api.finmindtrade.com/api/v4/data'
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJkYXRlIjoiMjAyNi0wMy0xMCAwMjowODoyMyIsInVzZXJfaWQiOiJxd2U2MDgxOCIsImVtYWlsIjoicXdlNjA4MThAaG90bWFpbC5jb20iLCJpcCI6IjEyMy4xOTQuMTg4LjEyOSJ9.qXBUvBVraRHJf4O4ANWerVEvqgTrw9uAHffUX7hphDQ'

# 75檔（移除表現最差的6檔：3054,2317,3095,2327,3171,3033）
popular_stocks = [
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
    # 獨立項目：華邦/威剛/新唐等（20檔）
    '2344', '2371', '2427', '2431', '2445', '2457', '2486', '3014', '3016', '3022',
    '3037', '3095', '3107', '3141', '3149', '3162', '3189', '3202', '3209', '6625'
]

def get_stock_data(stock_id, days=90):
    params = {
        'dataset': 'TaiwanStockPrice',
        'data_id': stock_id,
        'start_date': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
        'end_date': datetime.now().strftime('%Y-%m-%d'),
        'token': token
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        if data.get('success') and data.get('data'):
            return data['data']
    except:
        pass
    return None

def analyze_stock(stock_id):
    data = get_stock_data(stock_id)
    if not data or len(data) < 60:
        return None
    
    closes = [d['close'] for d in data]
    volumes = [d['Trading_Volume'] for d in data]
    
    price = closes[-1]
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes) / 60
    ma20_prev = sum(closes[-21:-1]) / 20 if len(closes) >= 21 else ma20
    vol_avg20 = sum(volumes[-20:]) / 20
    vol_today = volumes[-1]
    
    return {
        'stock': stock_id,
        'price': price,
        'ma20': ma20,
        'ma60': ma60,
        'ma20_up': ma20 > ma20_prev,
        'vol_ratio': vol_today / vol_avg20 if vol_avg20 > 0 else 0,
        'signal': price > ma20 > ma60 and ma20 > ma20_prev and vol_today > vol_avg20 * 1.2
    }

def scan_stocks(stocks=None, top_n=75):
    if stocks is None:
        stocks = popular_stocks[:top_n]
    
    print(f"正在分析 {len(stocks)} 檔股票...")
    results = []
    for i, stock in enumerate(stocks):
        result = analyze_stock(stock)
        if result:
            results.append(result)
        if (i + 1) % 10 == 0:
            print(f"  已分析 {i+1}/{len(stocks)} 檔")
    return results

def print_results(results):
    buy_signals = [r for r in results if r['signal']]
    
    print("\n" + "="*50)
    print("=== 台股短線策略 v5.0 掃描結果 ===")
    print(f"掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*50)
    
    if buy_signals:
        print("\n=== 符合買入訊號 ===")
        print("| 股票 | 股價 | MA20 | MA60 | MA20趨勢 | 量能 |")
        print("|------|------|------|------|----------|------|")
        for r in buy_signals:
            trend = "↑" if r['ma20_up'] else "↓"
            print(f"| {r['stock']} | {r['price']:.0f} | {r['ma20']:.0f} | {r['ma60']:.0f} | {trend} | {r['vol_ratio']:.2f}x |")
    else:
        print("\n今日無符合 v5.0 策略的買入訊號")

if __name__ == "__main__":
    top_n = 75
    for arg in sys.argv[1:]:
        if arg.isdigit():
            top_n = int(arg)
    
    results = scan_stocks(None, top_n)
    print_results(results)
