import pandas as pd
import os
import json
import sys
from dotenv import load_dotenv
import PyPDF2
import pdfplumber

VENDOR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.vendor')
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

# Charger les variables d'environnement
load_dotenv()

# Importer Gemini
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ Gemini non disponible. Installation : pip install google-genai")

class FundamentalAnalysis:
    """
    Analyse fondamentale avec LLM (Google Gemini)
    """
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.client = None
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        
        if GEMINI_AVAILABLE and self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            print("✅ Gemini initialisé")
        else:
            print("⚠️ Mode dégradé : analyse fondamentale simplifiée")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrait le texte d'un PDF de rapport financier"""
        text = ""
        
        try:
            # Essayer avec pdfplumber (meilleur pour tableaux)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages[:20]:  # Limiter aux 20 premières pages
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Si pdfplumber n'a rien extrait, essayer PyPDF2
            if not text.strip():
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages[:20]:
                        text += page.extract_text() + "\n"
            
            return text[:15000]  # Limiter pour ne pas dépasser les quotas API
            
        except Exception as e:
            print(f"Erreur extraction PDF : {e}")
            return ""
    
    def analyze_with_llm(self, text, company_name):
        """Analyse le texte avec Gemini pour extraire les données financières"""
        if not self.client:
            return self._fallback_analysis(company_name)
        
        prompt = f"""
        Analyse le rapport financier suivant de {company_name} et extrait les informations clés.
        
        Texte du rapport :
        {text}
        
        Réponds UNIQUEMENT au format JSON avec les champs suivants :
        {{
            "revenue": "chiffre d'affaires en FCFA (nombre sans virgule)",
            "net_income": "résultat net en FCFA (nombre sans virgule)",
            "total_assets": "total actif en FCFA (nombre sans virgule)",
            "shareholders_equity": "capitaux propres en FCFA (nombre sans virgule)",
            "eps": "bénéfice par action en FCFA (nombre)",
            "pe_ratio": "PER (nombre, si disponible)",
            "dividend_per_share": "dividende par action en FCFA (nombre)",
            "outlook": "perspectives pour l'année à venir (une phrase)",
            "risk_factors": "principaux facteurs de risque (une phrase)"
        }}
        
        Si une information n'est pas disponible, mets null.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json'
                )
            )
            # Extraire le JSON de la réponse
            response_text = response.text or ""
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                
                # Convertir les strings en nombres
                for key in ['revenue', 'net_income', 'total_assets', 'shareholders_equity']:
                    if data.get(key) and isinstance(data[key], str):
                        data[key] = float(data[key].replace(' ', '').replace(',', ''))
                
                return data
            else:
                return self._fallback_analysis(company_name)
                
        except Exception as e:
            print(f"Erreur analyse LLM : {e}")
            return self._fallback_analysis(company_name)
    
    def _fallback_analysis(self, company_name):
        """Analyse de secours quand LLM n'est pas disponible"""
        # Données simulées réalistes par entreprise
        fallback_data = {
            'BOAN': {'revenue': 250e9, 'net_income': 45e9, 'eps': 450, 'pe_ratio': 9.3},
            'ECOC': {'revenue': 180e9, 'net_income': 32e9, 'eps': 400, 'pe_ratio': 8.5},
            'NTLC': {'revenue': 90e9, 'net_income': 12e9, 'eps': 240, 'pe_ratio': 11.9},
            'SGBC': {'revenue': 320e9, 'net_income': 58e9, 'eps': 483, 'pe_ratio': 30.1},
            'ORANGE': {'revenue': 150e9, 'net_income': 25e9, 'eps': 357, 'pe_ratio': 10.0}
        }
        
        data = fallback_data.get(company_name, {
            'revenue': 100e9, 'net_income': 15e9, 'eps': 200, 'pe_ratio': 12
        }).copy()
        
        data['total_assets'] = data['revenue'] * 2
        data['shareholders_equity'] = data['revenue'] * 0.5
        data['dividend_per_share'] = data['eps'] * 0.4
        data['outlook'] = "Perspectives stables pour l'année à venir"
        data['risk_factors'] = "Concurrence et environnement réglementaire"
        
        return data
    
    def get_fundamental_data(self, ticker, current_price=None, report_path=None):
        """Obtenir les données fondamentales d'une entreprise"""
        
        if report_path and os.path.exists(report_path) and self.client:
            # Analyser le rapport financier
            text = self.extract_text_from_pdf(report_path)
            data = self.analyze_with_llm(text, ticker)
        else:
            # Utiliser l'analyse de secours
            data = self._fallback_analysis(ticker)
        
        # Calculer le PER si nécessaire
        if current_price and data.get('eps') and not data.get('pe_ratio'):
            data['pe_ratio'] = current_price / data['eps'] if data['eps'] > 0 else 0
        
        # Calculer le rendement du dividende
        if current_price and data.get('dividend_per_share'):
            data['dividend_yield'] = data['dividend_per_share'] / current_price
        
        data['ticker'] = ticker
        
        return data
    
    def get_financial_ratios(self, fundamental_data):
        """Calcule les ratios financiers supplémentaires"""
        ratios = {}
        
        if fundamental_data.get('revenue') and fundamental_data.get('net_income'):
            ratios['net_margin'] = fundamental_data['net_income'] / fundamental_data['revenue']
        
        if fundamental_data.get('net_income') and fundamental_data.get('total_assets'):
            ratios['roa'] = fundamental_data['net_income'] / fundamental_data['total_assets']
        
        if fundamental_data.get('net_income') and fundamental_data.get('shareholders_equity'):
            ratios['roe'] = fundamental_data['net_income'] / fundamental_data['shareholders_equity']
        
        return ratios