import MetaTrader5 as mt5

class Executor:
    """
    MT5 üzerinde emrin açılması, kapatılması ve
    Açık pozisyonların İzleyen Stop (Trailing Stop) ile takip edilmesinden sorumlu modül.
    """
    def __init__(self, magic_number: int = 100200):
        self.magic = magic_number  # Botun kendi açtığı işlemleri tanıması için kimlik kodu

    def get_filling_mode(self, symbol: str) -> int:
        """
        Aracı kurumun ve paritenin desteklediği en uygun emir dolgu modunu (Filling Mode) otomatik belirler.
        10030 (Unsupported filling mode) hatasını engeller.
        """
        info = mt5.symbol_info(symbol)
        if info is None:
            return mt5.ORDER_FILLING_IOC

        modes = info.filling_mode
        # Bitmask kontrolü: 1 = FOK, 2 = IOC, 4 = RETURN
        if modes & 1:
            return mt5.ORDER_FILLING_FOK
        elif modes & 2:
            return mt5.ORDER_FILLING_IOC
        elif modes & 4:
            return mt5.ORDER_FILLING_RETURN
        else:
            return mt5.ORDER_FILLING_RETURN

    def open_trade(self, symbol: str, signal: str, lot_size: float, sl_price: float, tp_price: float) -> bool:
        """
        Sinyale göre Piyasa Fiyatından (Market Order) emri açar.
        """
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"[-] {symbol} için anlık fiyat (tick) alınamadı.")
            return False

        order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if signal == "BUY" else tick.bid
        
        # Paritenin desteklediği dolgu modunu dinamik olarak çekiyoruz
        filling = self.get_filling_mode(symbol)

        # MT5 Emir Talebi Sözlüğü
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 20,              # Maksimum kayma (slippage) - 20 pip
            "magic": self.magic,
            "comment": "ForexBot_v1",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,       # Dinamik algılanan dolgu modu
        }

        # Emri MT5'e Gönder
        result = mt5.order_send(request)

        if result is None:
            print("[-] Emir Gönderilemedi! MT5 yanıt vermedi.")
            return False

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[-] Emir Başarısız! Hata Kodu: {result.retcode} | Açıklama: {result.comment}")
            return False

        print(f"[+] İŞLEM BAŞARILI! {signal} {lot_size} Lot {symbol} @ {price}")
        print(f"    -> Ticket ID: {result.order} | SL: {sl_price} | TP: {tp_price}")
        return True

    def manage_break_even(self, symbol: str, trigger_rr: float = 1.0):
        """
        Kârda olan açık pozisyonların Stop Loss seviyesini maliyete (Break-Even) çeker.
        """
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        for pos in positions:
            if pos.magic != self.magic:
                continue  # Botun açmadığı manuel işlemlere dokunma

            entry_price = pos.price_open
            current_sl = pos.sl
            tp_price = pos.tp
            
            # Alım Pozisyonu Kontrolü
            if pos.type == mt5.POSITION_TYPE_BUY:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    continue
                current_price = tick.bid
                sl_distance = abs(entry_price - current_sl)
                
                if (current_price >= entry_price + sl_distance * trigger_rr) and (current_sl < entry_price):
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "symbol": symbol,
                        "sl": entry_price,
                        "tp": tp_price
                    }
                    mt5.order_send(request)
                    print(f"[*] BREAK-EVEN UYGULANDI: Pozisyon #{pos.ticket} SL seviyesi maliyete ({entry_price}) taşındı!")

            # Satım Pozisyonu Kontrolü
            elif pos.type == mt5.POSITION_TYPE_SELL:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    continue
                current_price = tick.ask
                sl_distance = abs(current_sl - entry_price)

                if (current_price <= entry_price - sl_distance * trigger_rr) and (current_sl > entry_price):
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "symbol": symbol,
                        "sl": entry_price,
                        "tp": tp_price
                    }
                    mt5.order_send(request)
                    print(f"[*] BREAK-EVEN UYGULANDI: Pozisyon #{pos.ticket} SL seviyesi maliyete ({entry_price}) taşındı!")