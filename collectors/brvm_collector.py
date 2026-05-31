import pandas as pd
import random
from datetime import datetime, timedelta

class BRVMCollector:
    """
    Collecteur de données pour la BRVM
    Dans une version réelle : scraper les BOCs (tabula-py)
    Ici : générateur réaliste pour démonstration
    """
    
    def __init__(self):
        self.tickers = ['BOAN', 'ECOC', 'NTLC', 'SGBC', 'ORANGE']
        
    def get_historical_data(self, ticker, days=100):
        """Génère des données historiques simulées"""
        end_date = datetime.now()
        dates = [end_date - timedelta(days=i) for i in range(days)]
        dates.reverse()
        
        # Prix de départ réaliste
        base_price = {
            'BOAN': 4200, 'ECOC': 2400, 'NTLC': 1200,
            'SGBC': 8500, 'ORANGE': 2850
        }.get(ticker, 3000)
        
        prices = [base_price]
        for i in range(1, days):
            variation = random.uniform(-0.03, 0.04)
            new_price = prices[-1] * (1 + variation)
            prices.append(max(100, new_price))
        
        data = []
        for i, date in enumerate(dates):
            open_price = prices[i]
            close_price = prices[i] * (1 + random.uniform(-0.02, 0.02))
            high = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            volume = random.randint(5000, 200000)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def get_realtime_quote(self, ticker):
        """Simule un cours temps réel"""
        last_close = self.get_historical_data(ticker, days=1)['close'].iloc[-1]
        variation = random.uniform(-0.01, 0.01)
        current = last_close * (1 + variation)
        
        return {
            'ticker': ticker,
            'price': round(current, 2),
            'change': round((current - last_close) / last_close * 100, 2),
            'volume': random.randint(1000, 50000),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }