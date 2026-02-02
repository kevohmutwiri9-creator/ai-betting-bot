"""
Multi-language Support for AI Betting Bot
Supports English, Spanish, French, and German
"""

import json
from flask import request, session
from config import DEBUG_MODE

class I18nManager:
    def __init__(self):
        self.translations = {
            'en': {
                'dashboard': {
                    'title': 'AI Betting Assistant',
                    'last_updated': 'Last Updated',
                    'refresh': 'Refresh',
                    'total_analyzed': 'Total Analyzed',
                    'value_bets': 'Value Bets',
                    'success_rate': 'Success Rate',
                    'avg_roi': 'Average ROI',
                    'select_league': 'Select League',
                    'todays_value_bets': "Today's Value Bets",
                    'match_analyzer': 'Match Analyzer',
                    'auto_betting': 'Auto Betting',
                    'betting_history': 'Betting History',
                    'quick_actions': 'Quick Actions'
                },
                'leagues': {
                    'premier_league': 'Premier League',
                    'la_liga': 'La Liga',
                    'serie_a': 'Serie A',
                    'bundesliga': 'Bundesliga',
                    'ligue_1': 'Ligue 1',
                    'champions_league': 'Champions League',
                    'europa_league': 'Europa League',
                    'eredivisie': 'Eredivisie',
                    'casino_games': 'Casino Games',
                    'slot_games': 'Slot Games',
                    'poker_games': 'Poker Games',
                    'virtual_sports': 'Virtual Sports',
                    'esports': 'Esports'
                },
                'forms': {
                    'home_team': 'Home Team',
                    'away_team': 'Away Team',
                    'home_odds': 'Home Odds',
                    'draw_odds': 'Draw Odds',
                    'away_odds': 'Away Odds',
                    'analyze_match': 'Analyze Match',
                    'stake_per_bet': 'Stake per Bet (KES)',
                    'max_odds': 'Max Odds',
                    'min_value': 'Min Value (%)',
                    'auto_confirm': 'Auto Confirm',
                    'review_first': 'Review First',
                    'place_automatically': 'Place Automatically',
                    'start_auto_betting': 'Start Auto Betting',
                    'stop': 'Stop'
                },
                'messages': {
                    'loading_value_bets': 'Loading value bets...',
                    'no_value_bets': 'No value bets found at the moment',
                    'check_back_later': 'Check back later for new opportunities',
                    'loading_matches': 'Loading matches...',
                    'error_loading_matches': 'Error loading matches',
                    'auto_betting_started': 'Auto betting started successfully!',
                    'auto_betting_stopped': 'Auto betting stopped',
                    'auto_betting_failed': 'Auto betting failed',
                    'data_exported': 'Data exported successfully!',
                    'model_training_failed': 'Model training failed'
                },
                'betting': {
                    'pick': 'Pick',
                    'odds': 'Odds',
                    'value': 'Value',
                    'ev': 'EV',
                    'stake': 'Stake',
                    'profit': 'Profit',
                    'result': 'Result',
                    'won': 'Won',
                    'lost': 'Lost',
                    'confidence': 'Confidence',
                    'recommended_outcome': 'Recommended Outcome'
                }
            },
            'es': {
                'dashboard': {
                    'title': 'Asistente de Apuestas IA',
                    'last_updated': 'Última Actualización',
                    'refresh': 'Actualizar',
                    'total_analyzed': 'Total Analizado',
                    'value_bets': 'Apuestas de Valor',
                    'success_rate': 'Tasa de Éxito',
                    'avg_roi': 'ROI Promedio',
                    'select_league': 'Seleccionar Liga',
                    'todays_value_bets': 'Apuestas de Valor de Hoy',
                    'match_analyzer': 'Analizador de Partidos',
                    'auto_betting': 'Apuestas Automáticas',
                    'betting_history': 'Historial de Apuestas',
                    'quick_actions': 'Acciones Rápidas'
                },
                'leagues': {
                    'premier_league': 'Premier League',
                    'la_liga': 'La Liga',
                    'serie_a': 'Serie A',
                    'bundesliga': 'Bundesliga',
                    'ligue_1': 'Ligue 1',
                    'champions_league': 'Champions League',
                    'europa_league': 'Europa League',
                    'eredivisie': 'Eredivisie',
                    'casino_games': 'Juegos de Casino',
                    'slot_games': 'Tragamonedas',
                    'poker_games': 'Juegos de Póker',
                    'virtual_sports': 'Deportes Virtuales',
                    'esports': 'Esports'
                },
                'forms': {
                    'home_team': 'Equipo Local',
                    'away_team': 'Equipo Visitante',
                    'home_odds': 'Cuotas Local',
                    'draw_odds': 'Cuotas Empate',
                    'away_odds': 'Cuotas Visitante',
                    'analyze_match': 'Analizar Partido',
                    'stake_per_bet': 'Apuesta por Partido (KES)',
                    'max_odds': 'Cuotas Máximas',
                    'min_value': 'Valor Mínimo (%)',
                    'auto_confirm': 'Confirmar Automáticamente',
                    'review_first': 'Revisar Primero',
                    'place_automatically': 'Colocar Automáticamente',
                    'start_auto_betting': 'Iniciar Apuestas Automáticas',
                    'stop': 'Parar'
                },
                'messages': {
                    'loading_value_bets': 'Cargando apuestas de valor...',
                    'no_value_bets': 'No se encontraron apuestas de valor',
                    'check_back_later': 'Vuelve más tarde para nuevas oportunidades',
                    'loading_matches': 'Cargando partidos...',
                    'error_loading_matches': 'Error al cargar partidos',
                    'auto_betting_started': '¡Apuestas automátáticas iniciadas!',
                    'auto_betting_stopped': 'Apuestas automátáticas detenidas',
                    'auto_betting_failed': 'Falló el inicio de apuestas automátáticas',
                    'data_exported': '¡Datos exportados exitosamente!',
                    'model_training_failed': 'Falló el entrenamiento del modelo'
                },
                'betting': {
                    'pick': 'Selección',
                    'odds': 'Cuotas',
                    'value': 'Valor',
                    'ev': 'EV',
                    'stake': 'Apuesta',
                    'profit': 'Ganancia',
                    'result': 'Resultado',
                    'won': 'Ganado',
                    'lost': 'Perdido',
                    'confidence': 'Confianza',
                    'recommended_outcome': 'Resultado Recomendado'
                }
            },
            'fr': {
                'dashboard': {
                    'title': 'Assistant de Paris IA',
                    'last_updated': 'Dernière Mise à Jour',
                    'refresh': 'Actualiser',
                    'total_analyzed': 'Total Analysé',
                    'value_bets': 'Paris de Valeur',
                    'success_rate': 'Taux de Succès',
                    'avg_roi': 'ROI Moyen',
                    'select_league': 'Sélectionner la Ligue',
                    'todays_value_bets': 'Paris de Valeur du Jour',
                    'match_analyzer': 'Analyseur de Match',
                    'auto_betting': 'Paris Automatiques',
                    'betting_history': 'Historique des Paris',
                    'quick_actions': 'Actions Rapides'
                },
                'leagues': {
                    'premier_league': 'Premier League',
                    'la_liga': 'La Liga',
                    'serie_a': 'Serie A',
                    'bundesliga': 'Bundesliga',
                    'ligue_1': 'Ligue 1',
                    'champions_league': 'Ligue des Champions',
                    'europa_league': 'Ligue Europa',
                    'eredivisie': 'Eredivisie',
                    'casino_games': 'Jeux de Casino',
                    'slot_games': 'Machines à Sous',
                    'poker_games': 'Jeux de Poker',
                    'virtual_sports': 'Sports Virtuels',
                    'esports': 'Esports'
                },
                'forms': {
                    'home_team': 'Équipe à Domicile',
                    'away_team': 'Équipe Extérieure',
                    'home_odds': 'Cotes Domicile',
                    'draw_odds': 'Cotes Nul',
                    'away_odds': 'Cotes Extérieur',
                    'analyze_match': 'Analyser le Match',
                    'stake_per_bet': 'Mise par Paris (KES)',
                    'max_odds': 'Cotes Maximales',
                    'min_value': 'Valeur Minimale (%)',
                    'auto_confirm': 'Confirmation Automatique',
                    'review_first': 'Revoir d\'Abord',
                    'place_automatically': 'Placer Automatiquement',
                    'start_auto_betting': 'Démarrer les Paris Automatiques',
                    'stop': 'Arrêter'
                },
                'messages': {
                    'loading_value_bets': 'Chargement des paris de valeur...',
                    'no_value_bets': 'Aucun paris de valeur trouvé',
                    'check_back_later': 'Revenez plus tard pour de nouvelles opportunités',
                    'loading_matches': 'Chargement des matchs...',
                    'error_loading_matches': 'Erreur lors du chargement des matchs',
                    'auto_betting_started': 'Paris automatiques démarrés!',
                    'auto_betting_stopped': 'Paris automatiques arrêtés',
                    'auto_betting_failed': 'Échec du démarrage des paris automatiques',
                    'data_exported': 'Données exportées avec succès!',
                    'model_training_failed': 'Échec de l\'entraînement du modèle'
                },
                'betting': {
                    'pick': 'Sélection',
                    'odds': 'Cotes',
                    'value': 'Valeur',
                    'ev': 'EV',
                    'stake': 'Mise',
                    'profit': 'Profit',
                    'result': 'Résultat',
                    'won': 'Gagné',
                    'lost': 'Perdu',
                    'confidence': 'Confiance',
                    'recommended_outcome': 'Résultat Recommandé'
                }
            },
            'de': {
                'dashboard': {
                    'title': 'KI Wett-Assistent',
                    'last_updated': 'Zuletzt Aktualisiert',
                    'refresh': 'Aktualisieren',
                    'total_analyzed': 'Insgesamt Analysiert',
                    'value_bets': 'Value Wetten',
                    'success_rate': 'Erfolgsquote',
                    'avg_roi': 'Durchschnittlicher ROI',
                    'select_league': 'Liga Auswählen',
                    'todays_value_bets': 'Heutige Value Wetten',
                    'match_analyzer': 'Match-Analysator',
                    'auto_betting': 'Automatisches Wetten',
                    'betting_history': 'Wett-Historie',
                    'quick_actions': 'Schnelle Aktionen'
                },
                'leagues': {
                    'premier_league': 'Premier League',
                    'la_liga': 'La Liga',
                    'serie_a': 'Serie A',
                    'bundesliga': 'Bundesliga',
                    'ligue_1': 'Ligue 1',
                    'champions_league': 'Champions League',
                    'europa_league': 'Europa League',
                    'eredivisie': 'Eredivisie',
                    'casino_games': 'Casino Spiele',
                    'slot_games': 'Spielautomaten',
                    'poker_games': 'Poker Spiele',
                    'virtual_sports': 'Virtuelle Sportarten',
                    'esports': 'Esports'
                },
                'forms': {
                    'home_team': 'Heimteam',
                    'away_team': 'Auswärtsteam',
                    'home_odds': 'Heimquoten',
                    'draw_odds': 'Unentschiedenquoten',
                    'away_odds': 'Auswärtsquoten',
                    'analyze_match': 'Match Analysieren',
                    'stake_per_bet': 'Einsatz pro Wette (KES)',
                    'max_odds': 'Maximalquoten',
                    'min_value': 'Mindestwert (%)',
                    'auto_confirm': 'Automatisch Bestätigen',
                    'review_first': 'Zuerst Überprüfen',
                    'place_automatically': 'Automatisch Platzieren',
                    'start_auto_betting': 'Automatisches Wetten Starten',
                    'stop': 'Stopp'
                },
                'messages': {
                    'loading_value_bets': 'Lade Value Wetten...',
                    'no_value_bets': 'Keine Value Wetten gefunden',
                    'check_back_later': 'Später für neue Möglichkeiten zurückkehren',
                    'loading_matches': 'Lade Matches...',
                    'error_loading_matches': 'Fehler beim Laden der Matches',
                    'auto_betting_started': 'Automatisches Wetten gestartet!',
                    'auto_betting_stopped': 'Automatisches Wetten gestoppt',
                    'auto_betting_failed': 'Start des automatischen Wettens fehlgeschlagen',
                    'data_exported': 'Daten erfolgreich exportiert!',
                    'model_training_failed': 'Modell-Training fehlgeschlagen'
                },
                'betting': {
                    'pick': 'Auswahl',
                    'odds': 'Quoten',
                    'value': 'Wert',
                    'ev': 'EV',
                    'stake': 'Einsatz',
                    'profit': 'Gewinn',
                    'result': 'Ergebnis',
                    'won': 'Gewonnen',
                    'lost': 'Verloren',
                    'confidence': 'Vertrauen',
                    'recommended_outcome': 'Empfohlenes Ergebnis'
                }
            }
        }
        self.default_language = 'en'
        self.supported_languages = ['en', 'es', 'fr', 'de']
    
    def get_language(self):
        """Get current language from session or browser"""
        # Check session first
        if 'language' in session:
            return session['language']
        
        # Check browser language
        if request and hasattr(request, 'accept_languages'):
            browser_lang = request.accept_languages.best_match(self.supported_languages)
            if browser_lang:
                return browser_lang
        
        return self.default_language
    
    def set_language(self, language):
        """Set language in session"""
        if language in self.supported_languages:
            session['language'] = language
            return True
        return False
    
    def translate(self, key, language=None):
        """Translate a key to specified language"""
        if language is None:
            language = self.get_language()
        
        # Split key by dots (e.g., 'dashboard.title')
        keys = key.split('.')
        value = self.translations.get(language, {})
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            # Fallback to English
            value = self.translations.get(self.default_language, {})
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                # Return key if translation not found
                return key
    
    def get_translations_json(self, language=None):
        """Get all translations for a language as JSON"""
        if language is None:
            language = self.get_language()
        
        return json.dumps(self.translations.get(language, self.translations[self.default_language]))

# Flask integration
from flask import Blueprint

i18n_bp = Blueprint('i18n', __name__)
i18n_manager = I18nManager()

@i18n_bp.route('/api/language', methods=['POST'])
def set_language():
    """Set user language preference"""
    try:
        data = request.get_json()
        language = data.get('language', 'en')
        
        if i18n_manager.set_language(language):
            return jsonify({
                'success': True,
                'message': f'Language set to {language}',
                'translations': json.loads(i18n_manager.get_translations_json(language))
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported language'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@i18n_bp.route('/api/translations')
def get_translations():
    """Get translations for current language"""
    try:
        translations = i18n_manager.get_translations_json()
        return jsonify({
            'success': True,
            'data': json.loads(translations),
            'language': i18n_manager.get_language()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Template context processor
def inject_translations():
    """Inject translations into all templates"""
    return {
        't': lambda key: i18n_manager.translate(key),
        'current_language': i18n_manager.get_language(),
        'supported_languages': i18n_manager.supported_languages
    }
