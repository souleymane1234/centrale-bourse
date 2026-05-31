import pandas as pd
import numpy as np

class TechnicalAnalysis:
    
    @staticmethod
    def add_moving_averages(df, windows=[20, 50]):
        """Ajoute des moyennes mobiles"""
        for window in windows:
            df[f'SMA_{window}'] = df['close'].rolling(window=window).mean()
        return df
    
    @staticmethod
    def add_rsi(df, period=14):
        """Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def add_macd(df, fast=12, slow=26, signal=9):
        """MACD - Moving Average Convergence Divergence"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = ema_fast - ema_slow
        df['MACD_signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        return df
    
    @staticmethod
    def add_bollinger_bands(df, period=20, std_dev=2):
        """Bandes de Bollinger"""
        df['BB_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * std_dev)
        df['BB_lower'] = df['BB_middle'] - (bb_std * std_dev)
        return df
    
    @staticmethod
    def generate_signal(df):
        """Génère un signal d'achat/vente"""
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Logique simple
        buy_signals = 0
        sell_signals = 0
        
        # RSI
        if latest['RSI'] < 30:
            buy_signals += 1
        elif latest['RSI'] > 70:
            sell_signals += 1
        
        # MACD
        if latest['MACD'] > latest['MACD_signal'] and previous['MACD'] <= previous['MACD_signal']:
            buy_signals += 1
        elif latest['MACD'] < latest['MACD_signal'] and previous['MACD'] >= previous['MACD_signal']:
            sell_signals += 1
        
        # Prix vs SMA 50
        if latest['close'] > latest['SMA_50'] and previous['close'] <= previous['SMA_50']:
            buy_signals += 1
        elif latest['close'] < latest['SMA_50'] and previous['close'] >= previous['SMA_50']:
            sell_signals += 1
        
        if buy_signals >= 2:
            return "ACHAT"
        elif sell_signals >= 2:
            return "VENTE"
        else:
            return "NEUTRE"
    
    @staticmethod
    def run_full_analysis(df):
        """Execute toute l'analyse technique"""
        df = TechnicalAnalysis.add_moving_averages(df)
        df = TechnicalAnalysis.add_rsi(df)
        df = TechnicalAnalysis.add_macd(df)
        df = TechnicalAnalysis.add_bollinger_bands(df)
        signal = TechnicalAnalysis.generate_signal(df)
        
        return df, signal

    @staticmethod
    def serialize_series(df, limit=60):
        """Série temporelle des indicateurs pour les graphiques frontend."""
        if df is None or df.empty:
            return []

        tail = df.tail(limit)
        records = []
        for _, row in tail.iterrows():
            date_val = row.get("date")
            if hasattr(date_val, "strftime"):
                date_val = date_val.strftime("%Y-%m-%d")
            else:
                date_val = str(date_val)[:10]

            records.append(
                {
                    "date": date_val,
                    "close": TechnicalAnalysis._safe_float(row.get("close")),
                    "rsi": TechnicalAnalysis._safe_float(row.get("RSI")),
                    "macd": TechnicalAnalysis._safe_float(row.get("MACD")),
                    "macd_signal": TechnicalAnalysis._safe_float(row.get("MACD_signal")),
                    "macd_histogram": TechnicalAnalysis._safe_float(
                        row.get("MACD_histogram")
                    ),
                    "sma_20": TechnicalAnalysis._safe_float(row.get("SMA_20")),
                    "sma_50": TechnicalAnalysis._safe_float(row.get("SMA_50")),
                }
            )
        return records

    @staticmethod
    def _safe_float(value):
        if value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if np.isnan(number) or np.isinf(number):
            return None
        return round(number, 2)