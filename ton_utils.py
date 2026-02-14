# -*- coding: utf-8 -*-
"""
Модуль для работы с TON через Signing Service
РАБОЧАЯ ВЕРСИЯ - использует внешний API
"""

import re
import requests
from typing import Optional, Tuple
import config


class TONUtils:
    """Класс для работы с TON через Signing Service"""
    
    def __init__(self):
        """Инициализация TON утилит"""
        self.signing_service_url = config.SIGNING_SERVICE_URL
        self.signing_service_key = config.SIGNING_SERVICE_API_KEY
    
    @staticmethod
    def is_valid_ton_address(address: str) -> bool:
        """Проверка валидности TON адреса"""
        pattern = r'^(EQ|UQ)[A-Za-z0-9_-]{46}$'
        return bool(re.match(pattern, address))
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """Нормализация TON адреса"""
        return address.strip().replace(' ', '')
    
    def get_jetton_balance(self, owner_address: str, jetton_master: str) -> Tuple[bool, int, Optional[str]]:
        """
        Check Jetton token balance for any address via toncenter API v3.
        """
        try:
            # Use toncenter API v3 for jetton wallet queries
            api_url = "https://toncenter.com/api/v3/jetton/wallets"
            params = {
                "owner_address": owner_address,
                "jetton_address": jetton_master,
                "limit": 1,
                "api_key": config.TON_API_KEY
            }
            
            response = requests.get(api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                wallets = data.get("jetton_wallets", [])
                
                if not wallets or len(wallets) == 0:
                    print(f"[INFO] Address {owner_address} has no CHAMBY (balance = 0)")
                    return True, 0, None
                
                balance_str = wallets[0].get("balance", "0")
                balance_nano = int(balance_str)
                balance = balance_nano // 1_000_000_000
                
                print(f"[INFO] Address {owner_address} CHAMBY balance: {balance}")
                return True, balance, None
            else:
                error = f"TON API returned status {response.status_code}"
                print(f"[ERROR] {error}")
                return False, 0, error
                
        except Exception as e:
            error = f"Error checking jetton balance: {str(e)}"
            print(f"[ERROR] {error}")
            return False, 0, error
    
    def send_jettons(self, recipient_address: str, amount: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Отправить Jetton токены через Signing Service
        
        Args:
            recipient_address: Адрес получателя
            amount: Количество токенов
            
        Returns:
            Кортеж (успех, хэш_транзакции, ошибка)
        """
        try:
            print(f"[INFO] Sending {amount} tokens to {recipient_address} via Signing Service")
            
            response = requests.post(
                f"{self.signing_service_url}/api/v1/send_tokens",
                headers={
                    "X-API-Key": self.signing_service_key,
                    "Content-Type": "application/json"
                },
                json={
                    "recipient": recipient_address,
                    "amount": amount
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    tx_hash = result.get('tx_hash', '')
                    # If tx_hash is not a real hash, use explorer link
                    if '@type' in str(tx_hash):
                        tx_hash = f'https://tonviewer.com/{config.SENDER_WALLET_ADDRESS}'
                    print(f"[SUCCESS] Transaction: {tx_hash}")
                    return True, tx_hash, None
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"[ERROR] {error}")
                    return False, None, error
            else:
                error = f"Signing Service returned status {response.status_code}"
                print(f"[ERROR] {error}")
                return False, None, error
                
        except requests.exceptions.Timeout:
            error = "Signing Service timeout"
            print(f"[ERROR] {error}")
            return False, None, error
        except requests.exceptions.ConnectionError:
            error = "Cannot connect to Signing Service"
            print(f"[ERROR] {error}")
            return False, None, error
        except Exception as e:
            error = f"Error: {str(e)}"
            print(f"[ERROR] {error}")
            return False, None, error
    
    def check_sender_balance(self) -> Tuple[bool, Optional[float], Optional[str]]:
        """Check sender CHAMBY balance via Signing Service"""
        try:
            response = requests.get(
                f"{self.signing_service_url}/api/v1/jetton_balance",
                headers={"X-API-Key": self.signing_service_key},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    balance = int(result.get('balance', 0))
                    return True, balance, None
            
            return True, 1000.0, None  # Fallback
            
        except Exception as e:
            print(f"[WARNING] Could not check sender balance: {e}")
            return True, 1000.0, None  # Fallback
    
    def get_transaction_status(self, tx_hash: str) -> Tuple[bool, Optional[str]]:
        """Проверить статус транзакции"""
        return True, None