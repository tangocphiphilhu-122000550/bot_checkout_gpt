"""Database repository for CRUD operations"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from database.models import Account, Payment, CardBin, Proxy
from database.connection import get_database
from utils.logger import log


class AccountRepository:
    """Repository for Account operations"""
    
    @staticmethod
    def create(email: str, password: str, name: str = None, 
               birthdate: str = None, cookies: dict = None) -> bool:
        """Create new account"""
        db = get_database()
        
        with db.get_session() as session:
            account = Account(
                email=email,
                password=password,
                name=name,
                birthdate=birthdate,
                cookies=cookies
            )
            session.add(account)
            session.commit()
            
            log.success(f"✅ Account saved to database: {email}")
            return True
    
    @staticmethod
    def get_by_email(email: str) -> Optional[dict]:
        """Get account by email"""
        db = get_database()
        
        with db.get_session() as session:
            account = session.query(Account).filter(Account.email == email).first()
            if account:
                return {
                    'id': account.id,
                    'email': account.email,
                    'password': account.password,
                    'name': account.name,
                    'birthdate': account.birthdate,
                    'cookies': account.cookies,
                    'created_at': account.created_at,
                    'updated_at': account.updated_at
                }
            return None
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all accounts"""
        db = get_database()
        
        with db.get_session() as session:
            accounts = session.query(Account).order_by(Account.created_at.desc()).all()
            return [
                {
                    'id': a.id,
                    'email': a.email,
                    'password': a.password,
                    'name': a.name,
                    'birthdate': a.birthdate,
                    'cookies': a.cookies,
                    'created_at': a.created_at.isoformat() if a.created_at else None,
                    'updated_at': a.updated_at.isoformat() if a.updated_at else None
                }
                for a in accounts
            ]
    
    @staticmethod
    def update_cookies(email: str, cookies: dict) -> bool:
        """Update account cookies"""
        db = get_database()
        
        with db.get_session() as session:
            account = session.query(Account).filter(Account.email == email).first()
            if account:
                account.cookies = cookies
                account.updated_at = datetime.utcnow()
                return True
            return False
    
    @staticmethod
    def delete(email: str) -> bool:
        """Delete account"""
        db = get_database()
        
        with db.get_session() as session:
            account = session.query(Account).filter(Account.email == email).first()
            if account:
                session.delete(account)
                return True
            return False
    
    @staticmethod
    def count() -> int:
        """Count total accounts"""
        db = get_database()
        
        with db.get_session() as session:
            return session.query(Account).count()


class PaymentRepository:
    """Repository for Payment operations"""
    
    @staticmethod
    def create(account_email: str, workspace_name: str = None,
               checkout_session_id: str = None, payment_method_id: str = None,
               payment_status: str = None, success: bool = False,
               error: str = None) -> bool:
        """Create payment record"""
        db = get_database()
        
        with db.get_session() as session:
            payment = Payment(
                account_email=account_email,
                workspace_name=workspace_name,
                checkout_session_id=checkout_session_id,
                payment_method_id=payment_method_id,
                payment_status=payment_status,
                success=success,
                error=error
            )
            session.add(payment)
            session.commit()
            
            log.success(f"✅ Payment record saved: {account_email}")
            return True
    
    @staticmethod
    def get_by_account(account_email: str) -> List[dict]:
        """Get all payments for an account"""
        db = get_database()
        
        with db.get_session() as session:
            payments = session.query(Payment)\
                .filter(Payment.account_email == account_email)\
                .order_by(Payment.created_at.desc())\
                .all()
            
            return [
                {
                    'id': p.id,
                    'account_email': p.account_email,
                    'workspace_name': p.workspace_name,
                    'checkout_session_id': p.checkout_session_id,
                    'payment_method_id': p.payment_method_id,
                    'payment_status': p.payment_status,
                    'success': p.success,
                    'error': p.error,
                    'created_at': p.created_at.isoformat() if p.created_at else None
                }
                for p in payments
            ]
    
    @staticmethod
    def get_successful_payments() -> List[dict]:
        """Get all successful payments"""
        db = get_database()
        
        with db.get_session() as session:
            payments = session.query(Payment)\
                .filter(Payment.success == True)\
                .order_by(Payment.created_at.desc())\
                .all()
            
            return [
                {
                    'id': p.id,
                    'account_email': p.account_email,
                    'workspace_name': p.workspace_name,
                    'created_at': p.created_at.isoformat() if p.created_at else None
                }
                for p in payments
            ]
    
    @staticmethod
    def count_by_status(success: bool = True) -> int:
        """Count payments by status"""
        db = get_database()
        
        with db.get_session() as session:
            return session.query(Payment).filter(Payment.success == success).count()


class CardBinRepository:
    """Repository for CardBin operations"""
    
    @staticmethod
    def create(bin_number: str) -> bool:
        """Create or get existing BIN"""
        db = get_database()
        
        with db.get_session() as session:
            # Check if exists
            existing = session.query(CardBin).filter(CardBin.bin_number == bin_number).first()
            if existing:
                log.info(f"BIN already exists: {bin_number}")
                return True
            
            # Create new
            card_bin = CardBin(bin_number=bin_number)
            session.add(card_bin)
            session.commit()
            
            log.success(f"✅ BIN saved to database: {bin_number}")
            return True
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all BINs"""
        db = get_database()
        
        with db.get_session() as session:
            bins = session.query(CardBin)\
                .order_by(CardBin.success_count.desc())\
                .all()
            
            return [
                {
                    'id': b.id,
                    'bin_number': b.bin_number,
                    'success_count': b.success_count,
                    'fail_count': b.fail_count,
                    'last_used': b.last_used.isoformat() if b.last_used else None,
                    'created_at': b.created_at.isoformat() if b.created_at else None
                }
                for b in bins
            ]
    
    @staticmethod
    def update_success(bin_number: str):
        """Increment success count"""
        db = get_database()
        
        with db.get_session() as session:
            card_bin = session.query(CardBin).filter(CardBin.bin_number == bin_number).first()
            if card_bin:
                card_bin.success_count += 1
                card_bin.last_used = datetime.utcnow()
    
    @staticmethod
    def update_fail(bin_number: str):
        """Increment fail count"""
        db = get_database()
        
        with db.get_session() as session:
            card_bin = session.query(CardBin).filter(CardBin.bin_number == bin_number).first()
            if card_bin:
                card_bin.fail_count += 1
                card_bin.last_used = datetime.utcnow()
    
    @staticmethod
    def get_best_bins(limit: int = 10) -> List[dict]:
        """Get best performing BINs"""
        db = get_database()
        
        with db.get_session() as session:
            bins = session.query(CardBin)\
                .filter(CardBin.success_count > 0)\
                .order_by(CardBin.success_count.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    'id': b.id,
                    'bin_number': b.bin_number,
                    'success_count': b.success_count,
                    'fail_count': b.fail_count,
                    'last_used': b.last_used.isoformat() if b.last_used else None
                }
                for b in bins
            ]


class ProxyRepository:
    """Repository for Proxy operations"""
    
    @staticmethod
    def create(proxy_url: str, proxy_type: str = None, country: str = None,
               notes: str = None) -> bool:
        """Create or get existing proxy"""
        db = get_database()
        
        with db.get_session() as session:
            # Check if exists
            existing = session.query(Proxy).filter(Proxy.proxy_url == proxy_url).first()
            if existing:
                log.info(f"Proxy already exists: {proxy_url}")
                return True
            
            # Create new
            proxy = Proxy(
                proxy_url=proxy_url,
                proxy_type=proxy_type,
                country=country,
                notes=notes
            )
            session.add(proxy)
            session.commit()
            
            log.success(f"✅ Proxy saved to database: {proxy_url}")
            return True
    
    @staticmethod
    def get_all(active_only: bool = False) -> List[dict]:
        """Get all proxies"""
        db = get_database()
        
        with db.get_session() as session:
            query = session.query(Proxy)
            if active_only:
                query = query.filter(Proxy.is_active == True)
            proxies = query.order_by(Proxy.success_count.desc()).all()
            
            # Convert to dict to avoid detached instance errors
            return [
                {
                    'id': p.id,
                    'proxy_url': p.proxy_url,
                    'proxy_type': p.proxy_type,
                    'country': p.country,
                    'is_active': p.is_active,
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                    'response_time': p.response_time,
                    'success_rate': p.success_rate,
                    'last_used': p.last_used,
                    'last_check': p.last_check,
                    'notes': p.notes
                }
                for p in proxies
            ]
    
    @staticmethod
    def get_by_country(country: str, active_only: bool = True) -> List[dict]:
        """Get proxies by country"""
        db = get_database()
        
        with db.get_session() as session:
            query = session.query(Proxy).filter(Proxy.country == country)
            if active_only:
                query = query.filter(Proxy.is_active == True)
            proxies = query.order_by(Proxy.success_count.desc()).all()
            
            return [
                {
                    'id': p.id,
                    'proxy_url': p.proxy_url,
                    'proxy_type': p.proxy_type,
                    'country': p.country,
                    'is_active': p.is_active,
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                    'response_time': p.response_time,
                    'success_rate': p.success_rate
                }
                for p in proxies
            ]
    
    @staticmethod
    def get_best_proxy(country: str = None) -> Optional[dict]:
        """Get best performing proxy"""
        db = get_database()
        
        with db.get_session() as session:
            query = session.query(Proxy).filter(Proxy.is_active == True)
            if country:
                query = query.filter(Proxy.country == country)
            
            # Order by success rate (success_count / (success_count + fail_count))
            proxy = query.order_by(Proxy.success_count.desc()).first()
            
            if proxy:
                return {
                    'id': proxy.id,
                    'proxy_url': proxy.proxy_url,
                    'proxy_type': proxy.proxy_type,
                    'country': proxy.country,
                    'success_rate': proxy.success_rate,
                    'response_time': proxy.response_time
                }
            return None
    
    @staticmethod
    def update_success(proxy_url: str, response_time: int = None):
        """Increment success count"""
        db = get_database()
        
        with db.get_session() as session:
            proxy = session.query(Proxy).filter(Proxy.proxy_url == proxy_url).first()
            if proxy:
                proxy.success_count += 1
                proxy.last_used = datetime.utcnow()
                proxy.last_check = datetime.utcnow()
                if response_time:
                    proxy.response_time = response_time
    
    @staticmethod
    def update_fail(proxy_url: str):
        """Increment fail count"""
        db = get_database()
        
        with db.get_session() as session:
            proxy = session.query(Proxy).filter(Proxy.proxy_url == proxy_url).first()
            if proxy:
                proxy.fail_count += 1
                proxy.last_check = datetime.utcnow()
    
    @staticmethod
    def set_active(proxy_url: str, is_active: bool):
        """Set proxy active status"""
        db = get_database()
        
        with db.get_session() as session:
            proxy = session.query(Proxy).filter(Proxy.proxy_url == proxy_url).first()
            if proxy:
                proxy.is_active = is_active
                proxy.updated_at = datetime.utcnow()
    
    @staticmethod
    def delete(proxy_url: str) -> bool:
        """Delete proxy"""
        db = get_database()
        
        with db.get_session() as session:
            proxy = session.query(Proxy).filter(Proxy.proxy_url == proxy_url).first()
            if proxy:
                session.delete(proxy)
                session.commit()
                return True
            return False
    
    @staticmethod
    def delete_inactive() -> int:
        """Delete all inactive proxies"""
        db = get_database()
        
        with db.get_session() as session:
            count = session.query(Proxy).filter(Proxy.is_active == False).delete()
            session.commit()
            return count
    
    @staticmethod
    def delete_failed(min_fail_rate: float = 0.7) -> int:
        """Delete proxies with high fail rate"""
        db = get_database()
        
        with db.get_session() as session:
            proxies = session.query(Proxy).all()
            deleted = 0
            
            for proxy in proxies:
                total = proxy.success_count + proxy.fail_count
                if total > 5:  # Only consider proxies with at least 5 attempts
                    fail_rate = proxy.fail_count / total
                    if fail_rate >= min_fail_rate:
                        session.delete(proxy)
                        deleted += 1
            
            session.commit()
            return deleted
    
    @staticmethod
    def delete_all() -> int:
        """Delete all proxies"""
        db = get_database()
        
        with db.get_session() as session:
            count = session.query(Proxy).delete()
            session.commit()
            return count
    
    @staticmethod
    def count(active_only: bool = False) -> int:
        """Count proxies"""
        db = get_database()
        
        with db.get_session() as session:
            query = session.query(Proxy)
            if active_only:
                query = query.filter(Proxy.is_active == True)
            return query.count()


class KoreanAddressRepository:
    """Repository for KoreanAddress operations"""
    
    @staticmethod
    def create(line1: str, line2: str, city: str, postal_code: str, state: str) -> bool:
        """Create new address"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import KoreanAddress
            
            # Check if exists
            existing = session.query(KoreanAddress).filter(
                KoreanAddress.line1 == line1,
                KoreanAddress.postal_code == postal_code
            ).first()
            
            if existing:
                log.info(f"Address already exists: {line1}")
                return True
            
            address = KoreanAddress(
                line1=line1,
                line2=line2,
                city=city,
                postal_code=postal_code,
                state=state
            )
            session.add(address)
            session.commit()
            
            log.success(f"✅ Address saved: {city}, {line2}")
            return True
    
    @staticmethod
    def get_random_address(active_only: bool = True) -> Optional[dict]:
        """Get a random address"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import KoreanAddress
            
            query = session.query(KoreanAddress)
            if active_only:
                query = query.filter(KoreanAddress.is_active == True)
            
            # Get all addresses and pick random
            addresses = query.all()
            
            if not addresses:
                return None
            
            import random
            address = random.choice(addresses)
            
            # Update usage count
            address.usage_count += 1
            address.last_used = datetime.utcnow()
            session.commit()
            
            return {
                'line1': address.line1,
                'line2': address.line2,
                'city': address.city,
                'postal_code': address.postal_code,
                'state': address.state
            }
    
    @staticmethod
    def get_by_city(city: str, active_only: bool = True) -> Optional[dict]:
        """Get random address from specific city"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import KoreanAddress
            
            query = session.query(KoreanAddress).filter(KoreanAddress.city == city)
            if active_only:
                query = query.filter(KoreanAddress.is_active == True)
            
            addresses = query.all()
            
            if not addresses:
                return None
            
            import random
            address = random.choice(addresses)
            
            # Update usage count
            address.usage_count += 1
            address.last_used = datetime.utcnow()
            session.commit()
            
            return {
                'line1': address.line1,
                'line2': address.line2,
                'city': address.city,
                'postal_code': address.postal_code,
                'state': address.state
            }
    
    @staticmethod
    def get_all(active_only: bool = False) -> List[dict]:
        """Get all addresses"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import KoreanAddress
            
            query = session.query(KoreanAddress)
            if active_only:
                query = query.filter(KoreanAddress.is_active == True)
            
            addresses = query.order_by(KoreanAddress.usage_count.asc()).all()
            
            return [
                {
                    'id': a.id,
                    'line1': a.line1,
                    'line2': a.line2,
                    'city': a.city,
                    'postal_code': a.postal_code,
                    'state': a.state,
                    'usage_count': a.usage_count,
                    'last_used': a.last_used.isoformat() if a.last_used else None
                }
                for a in addresses
            ]
    
    @staticmethod
    def count(active_only: bool = False) -> int:
        """Count addresses"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import KoreanAddress
            
            query = session.query(KoreanAddress)
            if active_only:
                query = query.filter(KoreanAddress.is_active == True)
            return query.count()
    
    @staticmethod
    def set_active(address_id: int, is_active: bool):
        """Set address active status"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import KoreanAddress
            
            address = session.query(KoreanAddress).filter(KoreanAddress.id == address_id).first()
            if address:
                address.is_active = is_active
                session.commit()


class LogRepository:
    """Repository for Log operations"""
    
    @staticmethod
    def create(level: str, module: str, message: str, extra_data: dict = None) -> bool:
        """Create log entry"""
        try:
            db = get_database()
            
            with db.get_session() as session:
                from database.models import Log
                
                log_entry = Log(
                    level=level,
                    module=module,
                    message=message,
                    extra_data=extra_data
                )
                session.add(log_entry)
                session.commit()
                return True
        except Exception as e:
            # Don't log errors from logging to avoid infinite loop
            print(f"Failed to save log to database: {e}")
            return False
    
    @staticmethod
    def get_recent(limit: int = 100, level: str = None) -> List[dict]:
        """Get recent logs"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import Log
            
            query = session.query(Log)
            if level:
                query = query.filter(Log.level == level)
            
            logs = query.order_by(Log.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': l.id,
                    'level': l.level,
                    'module': l.module,
                    'message': l.message,
                    'extra_data': l.extra_data,
                    'created_at': l.created_at.isoformat() if l.created_at else None
                }
                for l in logs
            ]
    
    @staticmethod
    def get_by_module(module: str, limit: int = 100) -> List[dict]:
        """Get logs by module"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import Log
            
            logs = session.query(Log)\
                .filter(Log.module == module)\
                .order_by(Log.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                {
                    'id': l.id,
                    'level': l.level,
                    'module': l.module,
                    'message': l.message,
                    'extra_data': l.extra_data,
                    'created_at': l.created_at.isoformat() if l.created_at else None
                }
                for l in logs
            ]
    
    @staticmethod
    def get_errors(limit: int = 100) -> List[dict]:
        """Get error logs"""
        return LogRepository.get_recent(limit=limit, level='ERROR')
    
    @staticmethod
    def count_by_level(level: str) -> int:
        """Count logs by level"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import Log
            
            return session.query(Log).filter(Log.level == level).count()
    
    @staticmethod
    def delete_old_logs(days: int = 7) -> int:
        """Delete logs older than specified days"""
        db = get_database()
        
        with db.get_session() as session:
            from database.models import Log
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            count = session.query(Log).filter(Log.created_at < cutoff_date).delete()
            session.commit()
            return count
