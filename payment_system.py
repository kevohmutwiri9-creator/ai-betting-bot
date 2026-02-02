"""
Payment Processing System for AI Betting Bot
Handles premium subscriptions and payments via Stripe and PayPal
"""

import stripe
import paypalrestsdk
from flask import request, jsonify
from datetime import datetime, timedelta
import sqlite3
from auth import auth_manager
from config import (
    STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY, 
    PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET
)

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Initialize PayPal
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
    "client_id": PAYPAL_CLIENT_ID,
    "client_secret": PAYPAL_CLIENT_SECRET
})

class PaymentManager:
    def __init__(self, db_path="payments.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize payments database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                plan_type TEXT,
                amount REAL,
                currency TEXT,
                status TEXT,
                payment_provider TEXT,
                payment_id TEXT,
                started_at TEXT,
                ends_at TEXT,
                created_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subscription_id INTEGER,
                amount REAL,
                currency TEXT,
                status TEXT,
                payment_provider TEXT,
                payment_id TEXT,
                created_at TEXT,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_stripe_checkout_session(self, user_id, plan_type):
        """Create Stripe checkout session for premium subscription"""
        try:
            # Define pricing
            plans = {
                'monthly': {'price': 999, 'currency': 'usd', 'interval': 'month'},
                'yearly': {'price': 9999, 'currency': 'usd', 'interval': 'year'}
            }
            
            if plan_type not in plans:
                return {"success": False, "error": "Invalid plan type"}
            
            plan = plans[plan_type]
            
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan['currency'],
                        'product_data': {
                            'name': f'AI Betting Bot - {plan_type.title()} Premium',
                            'description': f'Premium subscription for AI Betting Bot ({plan_type})',
                        },
                        'unit_amount': plan['price'],
                        'recurring': {
                            'interval': plan['interval'],
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'https://yourwebsite.com/success?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'https://yourwebsite.com/cancel',
                metadata={
                    'user_id': str(user_id),
                    'plan_type': plan_type
                }
            )
            
            return {
                "success": True,
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_paypal_payment(self, user_id, plan_type):
        """Create PayPal payment for premium subscription"""
        try:
            # Define pricing
            plans = {
                'monthly': {'price': '9.99', 'currency': 'USD'},
                'yearly': {'price': '99.99', 'currency': 'USD'}
            }
            
            if plan_type not in plans:
                return {"success": False, "error": "Invalid plan type"}
            
            plan = plans[plan_type]
            
            # Create PayPal payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": f"https://yourwebsite.com/paypal/success",
                    "cancel_url": f"https://yourwebsite.com/paypal/cancel"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f"AI Betting Bot - {plan_type.title()} Premium",
                            "sku": f"premium_{plan_type}",
                            "price": plan['price'],
                            "currency": plan['currency'],
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": plan['price'],
                        "currency": plan['currency']
                    },
                    "description": f"Premium subscription for AI Betting Bot ({plan_type})"
                }]
            })
            
            if payment.create():
                for link in payment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    "success": True,
                    "approval_url": approval_url,
                    "payment_id": payment.id
                }
            else:
                return {"success": False, "error": payment.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def confirm_stripe_payment(self, session_id):
        """Confirm Stripe payment and activate subscription"""
        try:
            # Retrieve checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                user_id = int(session.metadata['user_id'])
                plan_type = session.metadata['plan_type']
                
                # Calculate subscription end date
                if plan_type == 'monthly':
                    ends_at = datetime.now() + timedelta(days=30)
                else:  # yearly
                    ends_at = datetime.now() + timedelta(days=365)
                
                # Save subscription to database
                self.save_subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    amount=session.amount_total / 100,  # Convert from cents
                    currency=session.currency,
                    payment_provider='stripe',
                    payment_id=session.payment_intent,
                    started_at=datetime.now().isoformat(),
                    ends_at=ends_at.isoformat()
                )
                
                # Upgrade user to premium
                auth_manager.upgrade_to_premium(user_id)
                
                return {"success": True, "message": "Subscription activated"}
            else:
                return {"success": False, "error": "Payment not completed"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def confirm_paypal_payment(self, payment_id, payer_id):
        """Confirm PayPal payment and activate subscription"""
        try:
            # Execute PayPal payment
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment.execute({"payer_id": payer_id}):
                # Extract user info (you'd need to store this during payment creation)
                # For now, we'll assume it's passed in metadata
                user_id = 1  # This should come from your payment creation process
                plan_type = 'monthly'  # This should come from your payment creation process
                
                # Calculate subscription end date
                if plan_type == 'monthly':
                    ends_at = datetime.now() + timedelta(days=30)
                else:  # yearly
                    ends_at = datetime.now() + timedelta(days=365)
                
                # Save subscription to database
                self.save_subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    amount=float(payment.transactions[0].amount.total),
                    currency=payment.transactions[0].amount.currency,
                    payment_provider='paypal',
                    payment_id=payment_id,
                    started_at=datetime.now().isoformat(),
                    ends_at=ends_at.isoformat()
                )
                
                # Upgrade user to premium
                auth_manager.upgrade_to_premium(user_id)
                
                return {"success": True, "message": "Subscription activated"}
            else:
                return {"success": False, "error": payment.error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_subscription(self, user_id, plan_type, amount, currency, payment_provider, payment_id, started_at, ends_at):
        """Save subscription to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO subscriptions 
            (user_id, plan_type, amount, currency, status, payment_provider, payment_id, started_at, ends_at, created_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
        ''', (user_id, plan_type, amount, currency, payment_provider, payment_id, started_at, ends_at, datetime.now().isoformat()))
        
        subscription_id = cursor.lastrowid
        
        # Save transaction
        cursor.execute('''
            INSERT INTO transactions 
            (user_id, subscription_id, amount, currency, status, payment_provider, payment_id, created_at)
            VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
        ''', (user_id, subscription_id, amount, currency, payment_provider, payment_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_user_subscriptions(self, user_id):
        """Get user's subscription history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'id': row[0],
                'user_id': row[1],
                'plan_type': row[2],
                'amount': row[3],
                'currency': row[4],
                'status': row[5],
                'payment_provider': row[6],
                'payment_id': row[7],
                'started_at': row[8],
                'ends_at': row[9],
                'created_at': row[10]
            })
        
        conn.close()
        return subscriptions

# Flask integration
from flask import Blueprint
from auth import require_auth

payment_bp = Blueprint('payment', __name__)
payment_manager = PaymentManager()

@payment_bp.route('/api/payment/create-stripe-session', methods=['POST'])
@require_auth
def create_stripe_session():
    """Create Stripe checkout session"""
    try:
        data = request.get_json()
        plan_type = data.get('plan_type', 'monthly')
        user_id = g.current_user['user_id']
        
        result = payment_manager.create_stripe_checkout_session(user_id, plan_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/api/payment/create-paypal-payment', methods=['POST'])
@require_auth
def create_paypal_payment():
    """Create PayPal payment"""
    try:
        data = request.get_json()
        plan_type = data.get('plan_type', 'monthly')
        user_id = g.current_user['user_id']
        
        result = payment_manager.create_paypal_payment(user_id, plan_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/api/payment/confirm-stripe', methods=['POST'])
def confirm_stripe_payment():
    """Confirm Stripe payment"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        result = payment_manager.confirm_stripe_payment(session_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/api/payment/confirm-paypal', methods=['POST'])
def confirm_paypal_payment():
    """Confirm PayPal payment"""
    try:
        data = request.get_json()
        payment_id = data.get('payment_id')
        payer_id = data.get('payer_id')
        
        result = payment_manager.confirm_paypal_payment(payment_id, payer_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@payment_bp.route('/api/payment/subscriptions')
@require_auth
def get_subscriptions():
    """Get user's subscriptions"""
    try:
        user_id = g.current_user['user_id']
        subscriptions = payment_manager.get_user_subscriptions(user_id)
        
        return jsonify({
            'success': True,
            'data': subscriptions
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
