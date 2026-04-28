import os
import requests
import json
import hashlib
import datetime
from app import app

def get_midtrans_config():
    """Get Midtrans configuration"""
    return {
        'server_key': app.config.get('MIDTRANS_SERVER_KEY', ''),
        'client_key': app.config.get('MIDTRANS_CLIENT_KEY', ''),
        'is_production': app.config.get('MIDTRANS_IS_PRODUCTION', False),
        'snap_url': app.config.get('MIDTRANS_SNAP_URL', 'https://app.snap-midtrans.com/snap/v1'),
        'api_url': app.config.get('MIDTRANS_API_URL', 'https://api.midtrans.com/v2'),
    }

def is_midtrans_enabled():
    """Check if Midtrans is configured"""
    config = get_midtrans_config()
    return bool(config['server_key'] and config['client_key'])

def generate_signature(order_id, amount):
    """Generate Midtrans signature"""
    config = get_midtrans_config()
    # Signature: SHA256(order_id + amount + server_key)
    signature = hashlib.sha256(
        f"{order_id}{int(amount)}{config['server_key']}".encode()
    ).hexdigest()
    return signature

def create_snap_token(order_id, amount, customer_details, item_details):
    """Create Snap payment token"""
    config = get_midtrans_config()
    
    if not config['server_key']:
        return {'success': False, 'message': 'Midtrans not configured'}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {config["server_key"]}',
    }
    
    payload = {
        'transaction_details': {
            'order_id': str(order_id),
            'gross_amount': int(amount),
        },
        'customer_details': customer_details,
        'item_details': item_details,
    }
    
    try:
        response = requests.post(
            f"{config['snap_url']}/token",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'token': data.get('token'),
                'redirect_url': data.get('redirect_url'),
            }
        else:
            return {
                'success': False,
                'message': f'Midtrans error: {response.status_code}'
            }
    except Exception as e:
        return {'success': False, 'message': str(e)}

def check_transaction_status(order_id):
    """Check Midtrans transaction status"""
    config = get_midtrans_config()
    
    if not config['server_key']:
        return {'success': False, 'message': 'Midtrans not configured'}
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {config["server_key"]}',
    }
    
    try:
        response = requests.get(
            f"{config['api_url']}/{order_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {'success': True, 'data': response.json()}
        else:
            return {'success': False, 'message': f'Error: {response.status_code}'}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def get_payment_methods():
    """Get available payment methods from Midtrans"""
    config = get_midtrans_config()
    
    if not is_midtrans_enabled():
        return []
    
    # Common payment methods
    return [
        {'code': 'credit_card', 'name': 'Kartu Kredit', 'icon': '💳'},
        {'code': 'mandiri_clickpay', 'name': 'Mandiri Clickpay', 'icon': '🏦'},
        {'code': 'bni_va', 'name': 'BNI VA', 'icon': '🏦'},
        {'code': 'bca_va', 'name': 'BCA VA', 'icon': '🏦'},
        {'code': 'bri_va', 'name': 'BRI VA', 'icon': '🏦'},
        {'code': 'alfamart', 'name': 'Alfamart', 'icon': '🏪'},
        {'code': 'indomaret', 'name': 'Indomaret', 'icon': '🏪'},
        {'code': 'shopeepay', 'name': 'ShopeePay', 'icon': '🛒'},
    ]

def get_midtrans_status_from_code(status_code):
    """Map Midtrans status to our payment status"""
    mapping = {
        'capture': 'confirmed',
        'settlement': 'confirmed',
        'pending': 'pending',
        'deny': 'failed',
        'expire': 'failed',
        'cancel': 'failed',
    }
    return mapping.get(status_code.lower(), 'pending')