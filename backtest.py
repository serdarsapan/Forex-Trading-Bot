import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta
import config

def run_pro_backtest(symbol: str = "GBPUSD", num_candles: int = 5000):
    if not mt5.initialize():
        print("[-] MT5 Bağlantı Hatası!")
        return

    mt5.symbol_select(symbol, True)
    print(f"\n==========================================")
    print(f"   PROFESYONEL SMC/PA BACKTEST: {symbol}")
    print(f"   İncelenen Mum Sayısı: {num_candles} (M15)")
    print(f"==========================================")

    rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, num_candles)
    rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, int(num_candles/16) + 100)

    if rates_m15 is None or rates_h4 is None:
        print("[-] Geçmiş veri çekilemedi.")
        mt5.shutdown()
        return

    df_m15 = pd.DataFrame(rates_m15)
    df_h4 = pd.DataFrame(rates_h4)
    
    df_m15['time'] = pd.to_datetime(df_m15['time'], unit='s')
    df_h4['time'] = pd.to_datetime(df_h4['time'], unit='s')

    # Trend Filtresi: EMA200
    df_h4['ema200'] = ta.ema(df_h4['close'], length=200)

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

        # H4 Güçlü Trend Kontrolü (EMA200)
        h4_sub = df_h4[df_h4['time'] <= current_time]
        if h4_sub.empty:
            continue
        last_h4 = h4_sub.iloc[-1]
        
        if pd.isna(last_h4['ema200']):
            continue

        h4_trend = "BULLISH" if last_h4['close'] > last_h4['ema200'] else "BEARISH"

        # 1. Açık Pozisyon Yönetimi (BE Esnekliği: 1.2 RR)
        if active_trade:
            sl_dist = abs(active_trade['entry'] - active_trade['initial_sl'])
            
            # Break-Even
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

        # 2. Yeni Sinyal Taraması (SMC / Swing High-Low Mantığı)
        if not active_trade:
            prev2 = df_m15.iloc[i-2]
            prev1 = df_m15.iloc[i-1]

            # Son 10 mumun tepe ve dip seviyeleri (Swing High / Swing Low)
            recent_high = df_m15.iloc[i-10:i-1]['high'].max()
            recent_low = df_m15.iloc[i-10:i-1]['low'].min()

            # Yapı Kırılımı Şartı (Break of Structure): Kapanan mum son 10 mumun tepesini/dibi geçmeli!
            bullish_bos = prev1['close'] > recent_high
            bearish_bos = prev1['close'] < recent_low

            bullish_eng = (prev2['close'] < prev2['open']) and (prev1['close'] > prev1['open']) and bullish_bos
            bearish_eng = (prev2['close'] > prev2['open']) and (prev1['close'] < prev1['open']) and bearish_bos

            if h4_trend == "BULLISH" and bullish_eng:
                # Stop seviyesini tam olarak son 10 mumun DİBİNE koyuyoruz (Mantıksal Stop)
                sl = recent_low - 0.0005 # 5 pip altına tampon
                sl_dist = abs(current_close - sl)

                if sl_dist > 0.0005: # Çok dar stopları engelle
                    tp = current_close + (sl_dist * config.RR_RATIO)
                    risk_usd = balance * (config.RISK_PER_TRADE / 100.0)

                    active_trade = {
                        "type": "BUY", "entry": current_close, "sl": sl, "initial_sl": sl, "tp": tp,
                        "risk_usd": risk_usd, "be_applied": False
                    }

            elif h4_trend == "BEARISH" and bearish_eng:
                # Stop seviyesini tam olarak son 10 mumun TEPE noktasına koyuyoruz
                sl = recent_high + 0.0005 # 5 pip üstüne tampon
                sl_dist = abs(sl - current_close)

                if sl_dist > 0.0005:
                    tp = current_close - (sl_dist * config.RR_RATIO)
                    risk_usd = balance * (config.RISK_PER_TRADE / 100.0)

                    active_trade = {
                        "type": "SELL", "entry": current_close, "sl": sl, "initial_sl": sl, "tp": tp,
                        "risk_usd": risk_usd, "be_applied": False
                    }

    mt5.shutdown()

    total_trades = len(trades)
    if total_trades == 0:
        print("[!] Seçilen filtrelerde hiç işlem oluşmadı.")
        return

    wins = len([t for t in trades if t['result'] == "WIN"])
    losses = len([t for t in trades if t['result'] == "LOSS"])
    bes = len([t for t in trades if t['result'] == "BE"])
    win_rate = (wins / total_trades) * 100
    net_profit = balance - initial_balance

    print(f"\n--- YENİ GERÇEKÇİ İSTATİSTİKLER ---")
    print(f"[*] Başlangıç Sermayesi : ${initial_balance:,.2f}")
    print(f"[*] Bitiş Sermayesi     : ${balance:,.2f}")
    print(f"[*] Net Kâr / Zarar     : ${net_profit:,.2f} ({((net_profit/initial_balance)*100):.2f}%)")
    print(f"[*] Toplam İşlem Sayısı : {total_trades}")
    print(f"[*] Kazanan (WIN)       : {wins}")
    print(f"[*] Kaybeden (LOSS)     : {losses}")
    print(f"[*] Başa Baş (BreakEven): {bes}")
    print(f"[*] Kazanma Oranı (%)   : %{win_rate:.1f}")
    print("==========================================\n")

if __name__ == "__main__":
    run_pro_backtest(symbol="GBPUSD", num_candles=5000)