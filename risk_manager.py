import pandas_ta as ta
import pandas as pd
import MetaTrader5 as mt5
import config

class RiskManager:
    """
    Sermaye, Risk ve Teminat (Margin) Yönetiminden sorumlu modül.
    """
    def __init__(self, risk_percent: float = 1.0, rr_ratio: float = 2.0):
        self.risk_percent = risk_percent
        self.rr_ratio = rr_ratio

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        atr_series = ta.atr(df['high'], df['low'], df['close'], length=period)
        return atr_series.iloc[-1]

    def check_margin_and_adjust_lot(self, symbol: str, signal: str, proposed_lot: float, entry_price: float) -> float:
        """
        Hesabın serbest teminatına (Free Margin) göre lot miktarını kontrol eder.
        Eğer teminat yetmiyorsa lotu serbest marjine uyacak şekilde küçültür.
        """
        account_info = mt5.account_info()
        if account_info is None:
            return proposed_lot

        free_margin = account_info.margin_free
        order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL

        # MT5'ten bu işlem için gereken teminatı sorgula
        required_margin = mt5.order_calc_margin(order_type, symbol, proposed_lot, entry_price)

        if required_margin is None:
            return proposed_lot

        # Kullanılabilir marjinin maksimum %70'ini tek bir işleme ayır (Emniyet marjı)
        max_allowed_margin = free_margin * 0.70

        # Eğer gereken teminat serbest marjinden büyükse lotu oranlayarak küçült
        if required_margin > max_allowed_margin and required_margin > 0:
            ratio = max_allowed_margin / required_margin
            adjusted_lot = round(proposed_lot * ratio, 2)
            adjusted_lot = max(getattr(config, 'MIN_LOT', 0.01), adjusted_lot)
            print(f"[!] DÜŞÜK MARJİN UYARISI: Hesaplanan Lot ({proposed_lot}) teminata göre {adjusted_lot} seviyesine düşürüldü.")
            return adjusted_lot

        return proposed_lot

    def get_trade_parameters(self, symbol: str, signal: str, entry_price: float, df_m15: pd.DataFrame, equity: float) -> dict:
        if signal == "HOLD" or equity <= 0:
            return None

        # 1. ATR Tabanlı SL/TP Mesafesi
        atr = self.calculate_atr(df_m15)
        sl_distance = atr * 1.5

        if signal == "BUY":
            sl_price = entry_price - sl_distance
            tp_price = entry_price + (sl_distance * self.rr_ratio)
        elif signal == "SELL":
            sl_price = entry_price + sl_distance
            tp_price = entry_price - (sl_distance * self.rr_ratio)

        # 2. Risk Tutarından Lot Hesaplama
        risk_amount_usd = equity * (self.risk_percent / 100.0)
        raw_lot = risk_amount_usd / (sl_distance * 100000)

        # 3. Config Limitleri Kontrolü (Min/Max Lot)
        min_lot = getattr(config, 'MIN_LOT', 0.01)
        max_lot = getattr(config, 'MAX_LOT', 0.50)
        bounded_lot = round(max(min_lot, min(raw_lot, max_lot)), 2)

        # 4. Teminat (Margin) Uygunluk Kontrolü
        final_lot = self.check_margin_and_adjust_lot(symbol, signal, bounded_lot, entry_price)

        return {
            "signal": signal,
            "entry_price": round(entry_price, 5),
            "sl_price": round(sl_price, 5),
            "tp_price": round(tp_price, 5),
            "risk_amount_usd": round(risk_amount_usd, 2),
            "lot_size": final_lot,
            "rr_ratio": self.rr_ratio
        }