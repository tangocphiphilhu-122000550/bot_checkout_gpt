"""Database models for Supabase"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Account(Base):
    """ChatGPT Account model"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(255))
    birthdate = Column(String(50))
    cookies = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'name': self.name,
            'birthdate': self.birthdate,
            'cookies': self.cookies,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_email = Column(String(255), nullable=False, index=True)
    workspace_name = Column(String(255))
    checkout_session_id = Column(String(500))
    payment_method_id = Column(String(500))
    payment_status = Column(String(100))
    success = Column(Boolean, default=False)
    error = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'account_email': self.account_email,
            'workspace_name': self.workspace_name,
            'checkout_session_id': self.checkout_session_id,
            'payment_method_id': self.payment_method_id,
            'payment_status': self.payment_status,
            'success': self.success,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CardBin(Base):
    """Card BIN storage"""
    __tablename__ = 'card_bins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bin_number = Column(String(20), unique=True, nullable=False, index=True)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'bin_number': self.bin_number,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class KoreanAddress(Base):
    """Korean address for payment"""
    __tablename__ = "korean_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    line1 = Column(String, nullable=False)
    line2 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    state = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'line1': self.line1,
            'line2': self.line2,
            'city': self.city,
            'postal_code': self.postal_code,
            'state': self.state,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Proxy(Base):
    """Proxy storage and management"""
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proxy_url = Column(String(500), unique=True, nullable=False, index=True)
    proxy_type = Column(String(50))  # http, socks5, etc.
    country = Column(String(10))  # KR, US, etc.
    is_active = Column(Boolean, default=True)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    last_check = Column(DateTime)
    response_time = Column(Integer)  # milliseconds
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'proxy_url': self.proxy_url,
            'proxy_type': self.proxy_type,
            'country': self.country,
            'is_active': self.is_active,
            'success_count': self.success_count,
            'fail_count': self.fail_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'response_time': self.response_time,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def success_rate(self):
        """Calculate success rate"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0
        return (self.success_count / total) * 100


class Log(Base):
    """Application logs storage"""
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, SUCCESS, DEBUG
    module = Column(String(100), index=True)  # Module name (e.g., payment.stripe_api)
    message = Column(String(2000), nullable=False)
    extra_data = Column(JSON)  # Additional context data
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'level': self.level,
            'module': self.module,
            'message': self.message,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
