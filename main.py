import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.brvm_collector import BRVMCollector
from analysis.technical import TechnicalAnalysis
from analysis.fundamental import FundamentalAnalysis
from reporting.report_generator import ReportGenerator
from storage.database import Database

def main():
    print("🚀 Lancement de l'agent d'analyse BRVM")
    
    # 1. Initialisation
    collector = BRVMCollector()
    db = Database()
    reporter = ReportGenerator()
    tech_analysis = TechnicalAnalysis()
    fund_analysis = FundamentalAnalysis()
    
    tickers = ['BOAN', 'ECOC', 'NTLC', 'SGBC', 'ORANGE']

    try:
        for ticker in tickers:
            print(f"\n📊 Analyse de {ticker}...")
            
            # 2. Collecte des données
            df = collector.get_historical_data(ticker, days=100)
            db.save_daily_prices(ticker, df)
            
            # 3. Analyse technique
            df_analyzed, signal = tech_analysis.run_full_analysis(df)
            current_price = df_analyzed.iloc[-1]['close']
            
            # 4. Données fondamentales
            fundamental_data = fund_analysis.get_fundamental_data(ticker, current_price=current_price)
            additional_ratios = fund_analysis.get_financial_ratios(fundamental_data)
            report_data = {**fundamental_data, **additional_ratios}
            
            # 5. Génération du graphique
            chart_path = reporter.generate_chart(df_analyzed, ticker)
            
            # 6. Génération du rapport HTML
            report_path = reporter.generate_html_report(
                ticker, df_analyzed, signal, report_data, chart_path
            )
            
            print(f"   ✅ Rapport généré : {report_path}")
            
            # 7. Affichage rapide dans le terminal
            latest = df_analyzed.iloc[-1]
            print(f"   📈 Prix : {latest['close']:.2f} FCFA | RSI : {latest['RSI']:.1f} | Signal : {signal}")
            print(f"   📊 PER : {report_data['pe_ratio']} | BPA : {report_data['eps']:.0f} FCFA")
    finally:
        db.close()

    print("\n✅ Analyse terminée. Consultez le dossier 'reports/' pour les rapports HTML.")

if __name__ == "__main__":
    main()