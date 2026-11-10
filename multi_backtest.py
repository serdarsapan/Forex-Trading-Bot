import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import config

def run_single_backtest(symbol: str, num_candles: int = 5000):
    mt5.symbol_select(symbol, True)
    
    rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, num_candles)
    rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, int(num_candles/16) + 100)

    if rates_m15 is None or rates_h4 is None:
        return None

    df_m15 = pd.DataFrame(rates_m15)
    df_h4 = pd.DataFrame(rates_h4)
    
    df_m15['time'] = pd.to_datetime(df_m15['time'], unit='s')
    df_h4['time'] = pd.to_datetime(df_h4['time'], unit='s')

    # Indicators
    df_h4['ema200'] = ta.ema(df_h4['close'], length=200)
    df_m15['atr'] = ta.atr(df_m15['high'], df_m15['low'], df_m15['close'], length=14)

    balance = 10000.0
    initial_balance = balance
    trades = []
    active_trade = None

    for i in range(50, len(df_m15) - 1):
        current_candle = df_m15.iloc[i]
        current_time = current_candle['time']
        current_close = current_candle['close']
        current_high = current_candle['high']
        current_low = current_candle['low']

        # H4 Trend Kontrolü
        h4_sub = df_h4[df_h4['time'] <= current_time]
        if h4_sub.empty:
            continue
        last_h4 = h4_sub.iloc[-1]
        
        if pd.isna(last_h4['ema200']):
            continue

        h4_trend = "BULLISH" if last_h4['close'] > last_h4['ema200'] else "BEARISH"

        # 1. Açık Pozisyon Yönetimi
        if active_trade:
            sl_dist = abs(active_trade['entry'] - active_trade['initial_sl'])
            
            # Break-Even Kontrolü
            if not active_trade['be_applied']:
                if active_trade['type'] == "BUY" and current_high >= active_trade['entry'] + (sl_dist * 1.2):
                    active_trade['sl'] = active_trade['entry']
                    active_trade['be_applied'] = True
                elif active_trade['type'] == "SELL" and current_low <= active_trade['entry'] - (sl_dist * 1.2):
                    active_trade['sl'] = active_trade['entry']
                    active_trade['be_applied'] = True

            # Pozisyon Kapanış
            if active_trade['type'] == "BUY":
                if current_low <= active_trade['sl']:
                    pnl = -active_trade['risk_usd'] if not active_trade['be_applied'] else 0.0
                    balance += pnl
                    trades.append({"type": "BUY", "result": "LOSS" if pnl < 0 else "BE", "pnl": pnl})
                    active_trade = None
                elif current_high >= active_trade['tp']:
                    pnl = active_trade['risk_usd'] * config.RR_RATIO
                    balance += pnl
                    trades.append({"type": "BUY", "result": "WIN", "pnl": pnl})
                    active_trade = None

            elif active_trade['type'] == "SELL":
                if current_high >= active_trade['sl']:
                    pnl = -active_trade['risk_usd'] if not active_trade['be_applied'] else 0.0
                    balance += pnl
                    trades.append({"type": "SELL", "result": "LOSS" if pnl < 0 else "BE", "pnl": pnl})
                    active_trade = None
                elif current_low <= active_trade['tp']:
                    pnl = active_trade['risk_usd'] * config.RR_RATIO
                    balance += pnl
                    trades.append({"type": "SELL", "result": "WIN", "pnl": pnl})
                    active_trade = None

        # 2. Yeni Sinyal Taraması
        if not active_trade:
            prev2 = df_m15.iloc[i-2]
            prev1 = df_m15.iloc[i-1]

            recent_high = df_m15.iloc[i-10:i-1]['high'].max()
            recent_low = df_m15.iloc[i-10:i-1]['low'].min()

            bullish_bos = prev1['close'] > recent_high
            bearish_bos = prev1['close'] < recent_low

            bullish_eng = (prev2['close'] < prev2['open']) and (prev1['close'] > prev1['open']) and bullish_bos
            bearish_eng = (prev2['close'] > prev2['open']) and (prev1['close'] < prev1['open']) and bearish_bos

            if h4_trend == "BULLISH" and bullish_eng:
                sl = recent_low - 0.0005
                sl_dist = abs(current_close - sl)

                if sl_dist > 0.0003:
                    tp = current_close + (sl_dist * config.RR_RATIO)
                    risk_usd = balance * (config.RISK_PER_TRADE / 100.0)

                    active_trade = {
                        "type": "BUY", "entry": current_close, "sl": sl, "initial_sl": sl, "tp": tp,
                        "risk_usd": risk_usd, "be_applied": False
                    }

            elif h4_trend == "BEARISH" and bearish_eng:
                sl = recent_high + 0.0005
                sl_dist = abs(sl - current_close)

                if sl_dist > 0.0003:
                    tp = current_close - (sl_dist * config.RR_RATIO)
                    risk_usd = balance * (config.RISK_PER_TRADE / 100.0)

                    active_trade = {
                        "type": "SELL", "entry": current_close, "sl": sl, "initial_sl": sl, "tp": tp,
                        "risk_usd": risk_usd, "be_applied": False
                    }

    total_trades = len(trades)
    if total_trades == 0:
        return {"symbol": symbol, "trades": 0, "win_rate": 0, "net_pnl": 0, "final_bal": initial_balance}

    wins = len([t for t in trades if t['result'] == "WIN"])
    losses = len([t for t in trades if t['result'] == "LOSS"])
    bes = len([t for t in trades if t['result'] == "BE"])
    win_rate = (wins / total_trades) * 100
    net_pnl = balance - initial_balance

    return {
        "symbol": symbol,
        "trades": total_trades,
        "wins": wins,
        "losses": losses,
        "bes": bes,
        "win_rate": round(win_rate, 1),
        "net_pnl": round(net_pnl, 2),
        "final_bal": round(balance, 2)
    }

def main():
    if not mt5.initialize():
        print("[-] MT5 Bağlantı Hatası!")
        return

    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    print(f"\n==========================================")
    print(f"   ÇOKLU PARİTE BACKTEST KARŞILAŞTIRMASI")
    print(f"   İncelenen Mum Sayısı: 5000 (M15)")
    print(f"==========================================\n")

    results = []
    for sym in symbols:
        res = run_single_backtest(sym, num_candles=5000)
        if res:
            results.append(res)

    mt5.shutdown()

    # Raporlama Tablosu
    print(f"{'Parite':<10} | {'İşlem':<8} | {'WIN':<5} | {'LOSS':<5} | {'BE':<5} | {'Win Rate (%)':<12} | {'Net Kâr/Zarar ($)':<16}")
    print("-" * 75)
    for r in results:
        print(f"{r['symbol']:<10} | {r['trades']:<8} | {r['wins']:<5} | {r['losses']:<5} | {r['bes']:<5} | %{r['win_rate']:<11} | ${r['net_pnl']:<15}")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()