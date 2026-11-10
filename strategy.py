import pandas as pd
import pandas_ta as ta
import config

class Strategy:
    """
    Forex strateji ve sinyal üretici sınıfı.
    Mum kapanışı (Default) ve Yüksek Konfeksiyonlu Canlı Mum (Erken Giriş) desteği barındırır.
    """
    def __init__(self, ema_period: int = 50):
        self.ema_period = ema_period

    def get_h4_trend(self, df_h4: pd.DataFrame) -> str:
        if df_h4.empty or len(df_h4) < self.ema_period:
            return "NEUTRAL"

        df_h4['ema'] = ta.ema(df_h4['close'], length=self.ema_period)
        last_candle = df_h4.iloc[-1]

        if last_candle['close'] > last_candle['ema']:
            return "BULLISH"
        elif last_candle['close'] < last_candle['ema']:
            return "BEARISH"
        
        return "NEUTRAL"

    def is_engulfing(self, df: pd.DataFrame, check_live_candle: bool = False) -> tuple[str, bool]:
        """
        Engulfing formasyonunu kontrol eder.
        - check_live_candle=False -> Varsayılan: Kapanmış mumları inceler (index -2 ve -3).
        - check_live_candle=True  -> Erken Giriş: Açık canlı mumu inceler (index -1 ve -2).
        
        Döndürür: (Formasyon_Tipi, Erken_Giriş_Mı)
        """
        if len(df) < 4:
            return "NONE", False

        # 1. VARSAYILAN KONTROL: Kapanmış Mumlar (Güvenli)
        prev_closed = df.iloc[-3]
        last_closed = df.iloc[-2]

        bullish_closed = (
            prev_closed['close'] < prev_closed['open'] and
            last_closed['close'] > last_closed['open'] and
            last_closed['close'] >= prev_closed['open'] and
            last_closed['open'] <= prev_closed['close']
        )

        bearish_closed = (
            prev_closed['close'] > prev_closed['open'] and
            last_closed['close'] < last_closed['open'] and
            last_closed['close'] <= prev_closed['open'] and
            last_closed['open'] >= prev_closed['close']
        )

        if bullish_closed:
            return "BULLISH_ENGULFING", False
        elif bearish_closed:
            return "BEARISH_ENGULFING", False

        # 2. İSTİSNAİ KONTROL: Canlı Mum Erken Giriş (Aşırı Momentum / Yüksek Konfeksiyon)
        if check_live_candle and getattr(config, 'ALLOW_EARLY_ENTRY', False):
            live_prev = df.iloc[-2]  # Son kapanan mum
            live_curr = df.iloc[-1]  # Şu an hareket eden canlı mum

            prev_body = abs(live_prev['close'] - live_prev['open'])
            curr_body = abs(live_curr['close'] - live_curr['open'])

            # Erken giriş için CANLI mum gövdesinin önceki muma oranı yeterince büyük mü?
            body_ratio_ok = (prev_body > 0) and ((curr_body / prev_body) >= config.EARLY_ENTRY_BODY_RATIO)

            # Canlı Boğa Yutan (Yüksek Momentum)
            bullish_live = (
                live_prev['close'] < live_prev['open'] and
                live_curr['close'] > live_curr['open'] and
                live_curr['close'] > live_prev['open'] and
                body_ratio_ok
            )

            # Canlı Ayı Yutan (Yüksek Momentum)
            bearish_live = (
                live_prev['close'] > live_prev['open'] and
                live_curr['close'] < live_curr['open'] and
                live_curr['close'] < live_prev['open'] and
                body_ratio_ok
            )

            if bullish_live:
                return "BULLISH_ENGULFING", True  # Erken giriş tetiklendi!
            elif bearish_live:
                return "BEARISH_ENGULFING", True  # Erken giriş tetiklendi!

        return "NONE", False

    def detect_wick_trap(self, df: pd.DataFrame) -> bool:
        if len(df) < 10:
            return False

        last_closed = df.iloc[-2]
        recent_high = df.iloc[-10:-2]['high'].max()
        recent_low = df.iloc[-10:-2]['low'].min()

        upward_sweep = (last_closed['high'] > recent_high) and (last_closed['close'] < recent_high)
        downward_sweep = (last_closed['low'] < recent_low) and (last_closed['close'] > recent_low)

        return upward_sweep or downward_sweep

    def analyze(self, df_m15: pd.DataFrame, df_h4: pd.DataFrame) -> dict:
        h4_trend = self.get_h4_trend(df_h4)
        
        # Öncelik 1: Kapanmış mum kontrolü (Varsayılan)
        m15_engulfing, is_early = self.is_engulfing(df_m15, check_live_candle=False)
        
        # Öncelik 2: Eğer kapanmış mumda sinyal yoksa, Canlı Mum Erken Giriş Şartlarını Tara
        if m15_engulfing == "NONE":
            m15_engulfing, is_early = self.is_engulfing(df_m15, check_live_candle=True)

        has_wick_trap = self.detect_wick_trap(df_m15)

        signal = "HOLD"
        reason = "Sinyal koşulları oluşmadı."

        # ALIM KOŞULLARI
        if h4_trend == "BULLISH" and m15_engulfing == "BULLISH_ENGULFING":
            if not has_wick_trap:
                signal = "BUY"
                type_str = "CANLI MUM ERKEN GİRİŞ (Yüksek Momentum)" if is_early else "Mum Kapanış Onaylı"
                reason = f"H4 Yükseliş Trendi + M15 Boğa Engulfing [{type_str}]"
            else:
                reason = "Boğa Engulfing var ancak Likit Tuzağı algılandı! İşlem elendi."

        # SATIM KOŞULLARI
        elif h4_trend == "BEARISH" and m15_engulfing == "BEARISH_ENGULFING":
            if not has_wick_trap:
                signal = "SELL"
                type_str = "CANLI MUM ERKEN GİRİŞ (Yüksek Momentum)" if is_early else "Mum Kapanış Onaylı"
                reason = f"H4 Düşüş Trendi + M15 Ayı Engulfing [{type_str}]"
            else:
                reason = "Ayı Engulfing var ancak Likit Tuzağı algılandı! İşlem elendi."

        return {
            "signal": signal,
            "h4_trend": h4_trend,
            "m15_pattern": m15_engulfing,
            "is_early_entry": is_early,
            "wick_trap": has_wick_trap,
            "reason": reason
        }