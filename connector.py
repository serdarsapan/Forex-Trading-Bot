import MetaTrader5 as mt5
import pandas as pd

class MT5Connector:
    """
    MetaTrader 5 ile iletişimden sorumlu bağlantı ve veri modülü.
    """
    def __init__(self, path: str = None):
        self.path = path
        # Zaman dilimi haritası
        self.tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }

    def initialize(self) -> bool:
        """MT5 terminaline bağlanır."""
        status = mt5.initialize(path=self.path) if self.path else mt5.initialize()
        if not status:
            print(f"[-] MT5 Bağlantı Hatası: {mt5.last_error()}")
            return False
        print("[+] MT5 Bağlantısı Başarıyla Kuruldu.")
        return True

    def get_rates(self, symbol: str, timeframe: str, count: int = 200) -> pd.DataFrame:
        """
        Belirtilen parite ve zaman diliminden mum verisi çeker ve
        analize uygun Pandas DataFrame formatına dönüştürür.
        """
        if timeframe not in self.tf_map:
            raise ValueError(f"Geçersiz zaman dilimi: {timeframe}. Geçerli olanlar: {list(self.tf_map.keys())}")

        tf = self.tf_map[timeframe]
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)

        if rates is None or len(rates) == 0:
            print(f"[-] {symbol} ({timeframe}) için veri alınamadı. Hata: {mt5.last_error()}")
            return pd.DataFrame()

        # Veriyi temizle ve yapılandır
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        return df

    def shutdown(self):
        """Bağlantıyı güvenli şekilde kapatır."""
        mt5.shutdown()
        print("[*] MT5 Oturumu Kapatıldı.")

    def get_account_equity(self) -> float:
        """Canlı hesap bakiyesini (Equity) getirir."""
        account_info = mt5.account_info()
        if account_info is None:
            print("[-] Bakiye bilgisi alınamadı.")
            return 0.0
        return account_info.equity

    def get_spread(self, symbol: str) -> float:
        """Paritenin anlık spread (makas) değerini pip cinsinden hesaplar."""
        info = mt5.symbol_info(symbol)
        if info is None:
            return 999.0
        # Pips hesaplaması (5 basamaklı pariteler için)
        spread_pips = info.spread / 10 if info.digits in [3, 5] else info.spread
        return round(spread_pips, 1)

    def get_open_positions_count(self) -> int:
        """Açık olan toplam pozisyon sayısını döndürür."""
        positions = mt5.positions_get()
        return len(positions) if positions else 0

    def has_open_position(self, symbol: str) -> bool:
        """Belirtilen paritede halihazırda açık pozisyon olup olmadığını kontrol eder."""
        positions = mt5.positions_get(symbol=symbol)
        return len(positions) > 0 if positions else False