import time
from datetime import datetime
import config
from connector import MT5Connector
from strategy import Strategy
from risk_manager import RiskManager
from executor import Executor
from news_filter import NewsFilter
from notifier import TelegramNotifier

def run_bot_cycle(connector, bot_brain, risk_engine, order_executor, news_guard, telegram):
    print(f"\n==========================================")
    print(f"   ÇOKLU TARAMA BAŞLADI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"==========================================")

    # Config Dosyasındaki Her Bir Parite İçin Bağımsız Döngü
    for symbol in config.SYMBOLS:
        print(f"\n---> [{symbol}] Analiz Ediliyor...")

        # 1. Parite Bazlı Açık Pozisyon Kontrolü
        # Eğer bu paritede zaten açık pozisyon varsa diğer pariteleri taramaya devam et!
        if connector.has_open_position(symbol):
            print(f"[*] {symbol} üzerinde zaten açık pozisyon var. Break-Even takibi yapılıyor...")
            order_executor.manage_break_even(symbol=symbol, trigger_rr=1.2)
            continue

        # 2. Spread (Makas) Kontrolü
        current_spread = connector.get_spread(symbol)
        if current_spread > config.MAX_SPREAD_PIPS:
            print(f"[-] {symbol} Spread Çok Yüksek: {current_spread} pips (Limit: {config.MAX_SPREAD_PIPS}). Pas geçildi.")
            continue

        # 3. Haber Şalteri Kontrolü
        has_news, news_reason = news_guard.is_news_time(symbol)
        if has_news:
            print(f"[!] {symbol} Haber Engeli: {news_reason}")
            continue

        # 4. Canlı Veri Çekme
        df_trend = connector.get_rates(symbol=symbol, timeframe=config.TREND_TIMEFRAME, count=100)
        df_trigger = connector.get_rates(symbol=symbol, timeframe=config.TRIGGER_TIMEFRAME, count=100)

        if not df_trend.empty and not df_trigger.empty:
            # Strateji Analizi
            analysis = bot_brain.analyze(df_m15=df_trigger, df_h4=df_trend)

            print(f"    * Spread: {current_spread} pips | Trend ({config.TREND_TIMEFRAME}): {analysis['h4_trend']}")
            print(f"    * Formasyon ({config.TRIGGER_TIMEFRAME}): {analysis['m15_pattern']}")
            print(f"    * Sinyal: {analysis['signal']} ({analysis['reason']})")

            # 5. Sinyal Varsa İşlem Aç
            if analysis['signal'] in ["BUY", "SELL"]:
                equity = connector.get_account_equity()
                current_close = df_trigger.iloc[-1]['close']

                trade_plan = risk_engine.get_trade_parameters(
                    symbol=symbol,
                    signal=analysis['signal'], 
                    entry_price=current_close, 
                    df_m15=df_trigger, 
                    equity=equity
                )

                if trade_plan:
                    print(f"\n[🚀] SİNYAL YAKALANDI: {symbol} -> {analysis['signal']}")
                    success = order_executor.open_trade(
                        symbol=symbol,
                        signal=trade_plan['signal'],
                        lot_size=trade_plan['lot_size'],
                        sl_price=trade_plan['sl_price'],
                        tp_price=trade_plan['tp_price']
                    )

                    if success:
                        msg = (f"<b>🚨 YENİ İŞLEM AÇILDI</b>\n\n"
                               f"<b>Parite:</b> {symbol}\n"
                               f"<b>Yön:</b> {trade_plan['signal']}\n"
                               f"<b>Lot:</b> {trade_plan['lot_size']}\n"
                               f"<b>Giriş:</b> {trade_plan['entry_price']}\n"
                               f"<b>SL:</b> {trade_plan['sl_price']}\n"
                               f"<b>TP (1:4 R:R):</b> {trade_plan['tp_price']}")
                        telegram.send_message(msg)
                        
def main():
    connector = MT5Connector()
    if not connector.initialize():
        return

    bot_brain = Strategy(ema_period=50)
    risk_engine = RiskManager(risk_percent=config.RISK_PER_TRADE, rr_ratio=config.RR_RATIO)
    order_executor = Executor(magic_number=100200)
    news_guard = NewsFilter(buffer_minutes=30)
    telegram = TelegramNotifier()

    print("[+] Esnek Çoklu Parite Botu Aktif!")
    print(f"[*] Takip Edilen Pariteler: {config.SYMBOLS}")
    print(f"[*] Zaman Dilimleri: Trend={config.TREND_TIMEFRAME}, Tetik={config.TRIGGER_TIMEFRAME}\n")

    try:
        while True:
            run_bot_cycle(connector, bot_brain, risk_engine, order_executor, news_guard, telegram)
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[-] Bot durduruldu.")
    finally:
        connector.shutdown()

if __name__ == "__main__":
    main()