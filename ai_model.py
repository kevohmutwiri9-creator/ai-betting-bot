import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
import sqlite3

class BettingAIModel:
    def __init__(self, model_path="betting_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_training_data(self, match_data):
        """Prepare data for training the AI model"""
        features = []
        labels = []
        
        for _, match in match_data.iterrows():
            # Calculate features
            home_strength = self.calculate_team_strength(match['home_team'])
            away_strength = self.calculate_team_strength(match['away_team'])
            
            # Feature vector
            feature_vector = [
                home_strength,
                away_strength,
                1.0,  # Home advantage
                match['home_odds'],
                match['draw_odds'],
                match['away_odds']
            ]
            
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
                labels.append(2 if match['home_odds'] < 2.5 else 0)
        
        return np.array(features), np.array(labels)
    
    def calculate_team_strength(self, team_name):
        """Calculate team strength based on historical performance"""
        # Simplified - in real app, query database
        team_strengths = {
            'Manchester United': 0.75,
            'Arsenal': 0.80,
            'Liverpool': 0.85,
            'Chelsea': 0.78,
            'Barcelona': 0.88,
            'Real Madrid': 0.90
        }
        return team_strengths.get(team_name, 0.5)
    
    def train_model(self, features, labels):
        """Train the RandomForest model"""
        print("Training AI model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model accuracy: {accuracy:.2f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        self.is_trained = True
        self.save_model()
        
        return accuracy
    
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
        except FileNotFoundError:
            print("No saved model found. Please train the model first.")
    
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
