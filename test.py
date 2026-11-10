import MetaTrader5 as mt5

# MT5 terminaline bağlanmayı dene
if mt5.initialize():
    print("Tebrikler! Python ve MetaTrader 5 başarıyla bağlandı.")
    print("MT5 Sürümü:", mt5.version())
    mt5.shutdown()
else:
    print("Bağlantı başarısız. Hata:", mt5.last_error())