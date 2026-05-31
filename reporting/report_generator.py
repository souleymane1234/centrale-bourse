import os
from datetime import datetime

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MPL_CONFIG_DIR = os.path.join(PROJECT_ROOT, '.matplotlib')
os.makedirs(MPL_CONFIG_DIR, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', MPL_CONFIG_DIR)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class ReportGenerator:
    
    def __init__(self, output_dir='reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_chart(self, df, ticker):
        """Génère un graphique des prix + indicateurs"""
        plt.figure(figsize=(12, 8))
        
        # Prix et SMA
        plt.subplot(2, 1, 1)
        plt.plot(df['date'], df['close'], label='Prix de clôture', color='black')
        plt.plot(df['date'], df['SMA_20'], label='SMA 20', linestyle='--', alpha=0.7)
        plt.plot(df['date'], df['SMA_50'], label='SMA 50', linestyle='--', alpha=0.7)
        plt.fill_between(df['date'], df['BB_upper'], df['BB_lower'], alpha=0.2, label='Bandes de Bollinger')
        plt.title(f'{ticker} - Analyse Technique')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # RSI
        plt.subplot(2, 1, 2)
        plt.plot(df['date'], df['RSI'], label='RSI', color='purple')
        plt.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Surchat (70)')
        plt.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Survente (30)')
        plt.fill_between(df['date'], 30, 70, alpha=0.1, color='gray')
        plt.title('Relative Strength Index (RSI)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_path = os.path.join(self.output_dir, f'{ticker}_chart.png')
        plt.savefig(chart_path)
        plt.close()
        
        return chart_path
    
    def generate_html_report(self, ticker, technical_df, technical_signal, fundamental_ratios, chart_path):
        """Génère un rapport HTML complet"""
        latest = technical_df.iloc[-1]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rapport d'analyse - {ticker}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 10px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                .signal {{ font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px; text-align: center; }}
                .ACHAT {{ background: #2ecc71; color: white; }}
                .VENTE {{ background: #e74c3c; color: white; }}
                .NEUTRE {{ background: #f39c12; color: white; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #3498db; color: white; }}
                .metrics {{ display: flex; gap: 20px; flex-wrap: wrap; }}
                .metric-card {{ background: #ecf0f1; padding: 15px; border-radius: 8px; flex: 1; min-width: 150px; }}
                .metric-value {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
                img {{ width: 100%; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Rapport d'analyse - {ticker}</h1>
                <p>Généré le : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="signal {technical_signal}">
                    Signal Technique : {technical_signal}
                </div>
                
                <h2>📈 Dernières données de marché</h2>
                <div class="metrics">
                    <div class="metric-card">💰 Prix<br><span class="metric-value">{latest['close']:,.2f} FCFA</span></div>
                    <div class="metric-card">📊 Volume<br><span class="metric-value">{latest['volume']:,}</span></div>
                    <div class="metric-card">⚡ RSI<br><span class="metric-value">{latest['RSI']:.1f}</span></div>
                    <div class="metric-card">📉 SMA 50<br><span class="metric-value">{latest['SMA_50']:,.2f}</span></div>
                </div>
                
                <h2>📊 Données fondamentales</h2>
                <div class="metrics">
                    <div class="metric-card">💰 CA<br><span class="metric-value">{fundamental_ratios['revenue']/1e9:.1f} Mds FCFA</span></div>
                    <div class="metric-card">📈 Bénéfice net<br><span class="metric-value">{fundamental_ratios['net_income']/1e9:.1f} Mds FCFA</span></div>
                    <div class="metric-card">💵 BPA<br><span class="metric-value">{fundamental_ratios['eps']:.0f} FCFA</span></div>
                    <div class="metric-card">🏷️ PER<br><span class="metric-value">{fundamental_ratios['pe_ratio']}</span></div>
                </div>
                
                <h2>📉 Analyse technique</h2>
                <img src="{chart_path}" alt="Graphique technique">
                
                <h2>📋 Derniers indicateurs</h2>
                <table>
                    <tr><th>Indicateur</th><th>Valeur</th><th>Interprétation</th></tr>
                    <tr><td>RSI (14)</td><td>{latest['RSI']:.1f}</td><td>{'Surchat ⚠️' if latest['RSI'] > 70 else 'Survente 📉' if latest['RSI'] < 30 else 'Neutre ✓'}</td></tr>
                    <tr><td>MACD</td><td>{latest['MACD']:.2f}</td><td>{'Tendance haussière' if latest['MACD'] > latest['MACD_signal'] else 'Tendance baissière'}</td></tr>
                    <tr><td>Prix vs SMA 50</td><td>{latest['close'] - latest['SMA_50']:.2f}</td><td>{'Au-dessus (' + str(round((latest['close']/latest['SMA_50']-1)*100,1)) + '%)' if latest['close'] > latest['SMA_50'] else 'En dessous (' + str(round((latest['close']/latest['SMA_50']-1)*100,1)) + '%)'}</td></tr>
                </table>
                
                <h2>📊 Recommandation</h2>
                <div class="signal {technical_signal}">
                    {self._get_recommendation_text(technical_signal, latest['RSI'], fundamental_ratios['pe_ratio'])}
                </div>
            </div>
        </body>
        </html>
        """
        
        report_path = os.path.join(self.output_dir, f'{ticker}_report.html')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return report_path
    
    def _get_recommendation_text(self, signal, rsi, pe_ratio):
        if signal == "ACHAT":
            return "✅ SIGNAL D'ACHAT - Les indicateurs techniques sont favorables. Surveillez les volumes."
        elif signal == "VENTE":
            return "⚠️ SIGNAL DE VENTE - Plusieurs indicateurs baissiers. Prudence recommandée."
        else:
            return "⏸️ SIGNAL NEUTRE - Pas de signal clair. Attendez une confirmation."