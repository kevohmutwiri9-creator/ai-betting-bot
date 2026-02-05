import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
import pickle
import sqlite3
import os
from datetime import datetime, timedelta
from collections import defaultdict

class BettingAIModel:
    def __init__(self, model_path="betting_model.pkl", db_path="betting_data.db"):
        self.model_path = model_path
        self.db_path = db_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.team_strengths_cache = {}
        self.cache_timeout = 3600  # 1 hour cache
        
    def calculate_team_strength(self, team_name, league=None, days_back=90):
        """Calculate team strength based on historical performance from database"""
        cache_key = f"{team_name}_{league or 'all'}_{days_back}"
        
        # Check cache first
        if cache_key in self.team_strengths_cache:
            cached_time, strength = self.team_strengths_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return strength
        
        # Query database for historical performance
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Calculate performance for home games
        cursor.execute('''
            SELECT 
                COUNT(*) as matches,
                SUM(CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END) as losses,
                SUM(home_goals) as goals_scored,
                SUM(away_goals) as goals_conceded
            FROM matches 
            WHERE home_team = ? AND date >= ?
        ''', (team_name, cutoff_date))
        
        home_stats = cursor.fetchone()
        
        # Calculate performance for away games
        cursor.execute('''
            SELECT 
                COUNT(*) as matches,
                SUM(CASE WHEN away_goals > home_goals THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN away_goals = home_goals THEN 1 ELSE 0 END) as draws,
                SUM(CASE WHEN away_goals < home_goals THEN 1 ELSE 0 END) as losses,
                SUM(away_goals) as goals_scored,
                SUM(home_goals) as goals_conceded
            FROM matches 
            WHERE away_team = ? AND date >= ?
        ''', (team_name, cutoff_date))
        
        away_stats = cursor.fetchone()
        conn.close()
        
        # Default values for new/unknown teams
        if home_stats[0] == 0 and away_stats[0] == 0:
            # Use league-average performance with slight random variation
            return self._get_default_strength()
        
        # Combine home and away stats
        total_matches = home_stats[0] + away_stats[0]
        total_wins = home_stats[1] + away_stats[1]
        total_draws = home_stats[2] + away_stats[2]
        total_losses = home_stats[3] + away_stats[3]
        total_goals_scored = home_stats[4] + away_stats[4]
        total_goals_conceded = home_stats[5] + away_stats[5]
        
        if total_matches == 0:
            return self._get_default_strength()
        
        # Calculate strength score (0-1 scale)
        win_rate = total_wins / total_matches
        draw_rate = total_draws / total_matches
        loss_rate = total_losses / total_matches
        
        goal_difference = (total_goals_scored - total_goals_conceded) / total_matches
        goals_per_match = total_goals_scored / total_matches
        
        # Weighted strength calculation
        strength = (win_rate * 0.5 + 
                   (1 - loss_rate) * 0.2 + 
                   min(goal_difference + 1, 2) / 2 * 0.2 + 
                   min(goals_per_match / 3, 1) * 0.1)
        
        # Clamp to reasonable range
        strength = max(0.2, min(0.95, strength))
        
        # Cache the result
        self.team_strengths_cache[cache_key] = (datetime.now(), strength)
        
        return strength
    
    def _get_default_strength(self):
        """Return default strength for unknown teams"""
        return 0.5
    
    def calculate_form(self, team_name, league=None, matches=5):
        """Calculate recent form (last N matches)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last N home matches
        cursor.execute('''
            SELECT home_goals, away_goals 
            FROM matches 
            WHERE home_team = ? 
            ORDER BY date DESC 
            LIMIT ?
        ''', (team_name, matches))
        
        home_matches = cursor.fetchall()
        
        # Get last N away matches
        cursor.execute('''
            SELECT away_goals, home_goals 
            FROM matches 
            WHERE away_team = ? 
            ORDER BY date DESC 
            LIMIT ?
        ''', (team_name, matches))
        
        away_matches = cursor.fetchall()
        conn.close()
        
        # Calculate form score (points from last N matches)
        form_score = 0
        total_matches = 0
        
        for goals_for, goals_against in home_matches:
            if goals_for > goals_against:
                form_score += 3
            elif goals_for == goals_against:
                form_score += 1
            total_matches += 1
        
        for goals_for, goals_against in away_matches:
            if goals_for > goals_against:
                form_score += 3
            elif goals_for == goals_against:
                form_score += 1
            total_matches += 1
        
        if total_matches == 0:
            return 0.5  # Default form
        
        return (form_score / (total_matches * 3))  # Normalize to 0-1
    
    def calculate_head_to_head(self, home_team, away_team, matches=10):
        """Calculate head-to-head performance between two teams"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT home_goals, away_goals 
            FROM matches 
            WHERE (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
            ORDER BY date DESC 
            LIMIT ?
        ''', (home_team, away_team, away_team, home_team, matches))
        
        h2h_matches = cursor.fetchall()
        conn.close()
        
        if not h2h_matches:
            return {'home_wins': 0, 'away_wins': 0, 'draws': 0, 'avg_goals': 0}
        
        home_wins = sum(1 for h, a in h2h_matches if h > a)
        away_wins = sum(1 for h, a in h2h_matches if a > h)
        draws = sum(1 for h, a in h2h_matches if h == a)
        avg_goals = sum(h + a for h, a in h2h_matches) / len(h2h_matches)
        
        return {
            'home_wins': home_wins,
            'away_wins': away_wins,
            'draws': draws,
            'avg_goals': avg_goals
        }
    
    def train_model(self, features, labels, use_ensemble=True, hyperparameter_tuning=False):
        """Train the AI model with optional ensemble and hyperparameter tuning"""
        print("Training AI model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        if use_ensemble:
            # Train ensemble of models
            from sklearn.ensemble import VotingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.svm import SVC
            
            rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
            lr = LogisticRegression(max_iter=1000, random_state=42)
            
            self.model = VotingClassifier(
                estimators=[('rf', rf), ('gb', gb), ('lr', lr)],
                voting='soft'  # Use probability averaging
            )
        else:
            if hyperparameter_tuning:
                # Perform hyperparameter tuning
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10]
                }
                
                grid_search = GridSearchCV(
                    RandomForestClassifier(random_state=42),
                    param_grid,
                    cv=5,
                    scoring='accuracy',
                    n_jobs=-1
                )
                grid_search.fit(X_train_scaled, y_train)
                
                self.model = grid_search.best_estimator_
                print(f"Best parameters: {grid_search.best_params_}")
            else:
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        print(f"Model accuracy: {accuracy:.2f}")
        print(f"Cross-validation scores: {cv_scores.mean():.2f} (+/- {cv_scores.std() * 2:.2f})")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        self.is_trained = True
        self.save_model()
        
        return accuracy
    
    def prepare_training_data(self, match_data, include_form=True, include_h2h=True):
        """Prepare data for training with enhanced features"""
        features = []
        labels = []
        
        for _, match in match_data.iterrows():
            # Calculate base features
            home_strength = self.calculate_team_strength(match['home_team'], match.get('league'))
            away_strength = self.calculate_team_strength(match['away_team'], match.get('league'))
            
            # Build feature vector
            feature_vector = [
                home_strength,
                away_strength,
                1.0,  # Home advantage
                float(match['home_odds']) if match.get('home_odds') not in [None, '', 'N/A'] else 2.5,
                float(match['draw_odds']) if match.get('draw_odds') not in [None, '', 'N/A'] else 3.2,
                float(match['away_odds']) if match.get('away_odds') not in [None, '', 'N/A'] else 2.8
            ]
            
            # Add form features if enabled
            if include_form:
                home_form = self.calculate_form(match['home_team'], match.get('league'))
                away_form = self.calculate_form(match['away_team'], match.get('league'))
                feature_vector.extend([home_form, away_form])
            
            # Add head-to-head features if enabled
            if include_h2h:
                h2h = self.calculate_head_to_head(match['home_team'], match['away_team'])
                total_h2h = h2h['home_wins'] + h2h['away_wins'] + h2h['draws']
                if total_h2h > 0:
                    h2h_home_ratio = (h2h['home_wins'] + 0.5 * h2h['draws']) / total_h2h
                    h2h_goals = h2h['avg_goals']
                else:
                    h2h_home_ratio = 0.5
                    h2h_goals = 2.5
                feature_vector.extend([h2h_home_ratio, h2h_goals])
            
            features.append(feature_vector)
            
            # Label: 0=away win, 1=draw, 2=home win (based on actual results)
            if 'home_goals' in match and 'away_goals' in match:
                if match['home_goals'] > match['away_goals']:
                    labels.append(2)  # Home win
                elif match['home_goals'] == match['away_goals']:
                    labels.append(1)  # Draw
                else:
                    labels.append(0)  # Away win
            else:
                # For prediction, use odds to simulate labels
                home_odds = float(match['home_odds']) if match.get('home_odds') not in [None, '', 'N/A'] else 2.5
                labels.append(2 if home_odds < 2.5 else 0)
        
        return np.array(features), np.array(labels)
    
    def predict_match_outcome(self, match_features):
        """Predict probability of match outcomes"""
        if not self.is_trained:
            self.load_model()
        
        if self.model is None:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Scale features
        features_scaled = self.scaler.transform([match_features])
        
        # Get probabilities
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        return {
            'away_win_prob': probabilities[0],
            'draw_prob': probabilities[1],
            'home_win_prob': probabilities[2]
        }
    
    def save_model(self):
        """Save trained model to file"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model from file"""
        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            
            print(f"Model loaded from {self.model_path}")
        except (FileNotFoundError, ModuleNotFoundError, ImportError) as e:
            print(f"Could not load model ({e}). Training new model...")
            self.train_model(self.generate_sample_training_data(500), np.array([0] * 500))
        except Exception as e:
            print(f"Model loading error: {e}. Training new model...")
            self.train_model(self.generate_sample_training_data(500), np.array([0] * 500))
    
    def generate_sample_training_data(self, num_samples=500):
        """Generate sample training data for demonstration"""
        np.random.seed(42)
        
        teams = ['Manchester United', 'Arsenal', 'Liverpool', 'Chelsea', 'Barcelona', 'Real Madrid']
        
        data = []
        for i in range(num_samples):
            home_team = np.random.choice(teams)
            away_team = np.random.choice([t for t in teams if t != home_team])
            
            # Simulate match data
            home_strength = self.calculate_team_strength(home_team)
            away_strength = self.calculate_team_strength(away_team)
            
            # Generate odds based on team strengths
            strength_diff = home_strength - away_strength
            home_odds = max(1.2, 3.0 - strength_diff * 2 + np.random.normal(0, 0.2))
            away_odds = max(1.2, 3.0 + strength_diff * 2 + np.random.normal(0, 0.2))
            draw_odds = max(2.5, 3.5 + np.random.normal(0, 0.3))
            
            # Simulate match result
            home_goals = np.random.poisson(home_strength * 2)
            away_goals = np.random.poisson(away_strength * 1.8)
            
            data.append({
                'home_team': home_team,
                'away_team': away_team,
                'home_odds': round(home_odds, 2),
                'draw_odds': round(draw_odds, 2),
                'away_odds': round(away_odds, 2),
                'home_goals': home_goals,
                'away_goals': away_goals
            })
        
        return pd.DataFrame(data)

if __name__ == "__main__":
    # Initialize model
    ai_model = BettingAIModel()
    
    # Generate sample training data
    training_data = ai_model.generate_sample_training_data(200)
    print(f"Generated {len(training_data)} training samples")
    
    # Prepare data
    features, labels = ai_model.prepare_training_data(training_data)
    
    # Train model
    accuracy = ai_model.train_model(features, labels)
    
    # Test prediction
    sample_match = [0.75, 0.80, 1.0, 2.10, 3.40, 3.20]  # Man Utd vs Arsenal
    prediction = ai_model.predict_match_outcome(sample_match)
    print(f"\nSample prediction: {prediction}")
