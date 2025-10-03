"""
Oracle Autonomous Database Data Service
Fetches precipitation and weather data from Oracle ATP
"""

import oracledb
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import warnings

# Suppress pandas SQLAlchemy warning for oracledb
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy')

logger = logging.getLogger(__name__)


class OracleDataService:
    """Service to fetch data from Oracle Autonomous Database"""
    
    def __init__(self):
        """Initialize Oracle ATP connection"""
        self.user = os.getenv('ORACLE_USER', 'admin')
        self.password = os.getenv('ORACLE_PASSWORD')
        self.dsn = os.getenv('ORACLE_DSN', 'hk005k69b4rnpald_high')
        self.wallet_location = os.getenv('ORACLE_WALLET_LOCATION', '/home/ongera/oracle_wallet')
        
        self.connection = None
        self._connection_attempted = False
        
        # Don't connect immediately - connect on first use
        if self.password:
            self._connect()
    
    def _connect(self):
        """Establish connection to Oracle ATP using thin mode"""
        if self._connection_attempted:
            return
        
        self._connection_attempted = True
        
        try:
            if not self.password:
                logger.warning("Oracle password not set, skipping connection")
                return
            
            # Use thin mode (no Oracle Client installation required)
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn,
                config_dir=self.wallet_location,
                wallet_location=self.wallet_location,
                wallet_password="WalletPassword123!"
            )
            logger.info(f"✓ Connected to Oracle ATP: {self.dsn}")
            
        except Exception as e:
            logger.error(f"Oracle ATP connection failed: {e}")
            logger.error(f"  User: {self.user}, DSN: {self.dsn}, Wallet: {self.wallet_location}")
            self.connection = None
    
    def is_available(self) -> bool:
        """Check if Oracle ATP is available"""
        return self.connection is not None
    
    def get_precipitation_data(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Get precipitation data from Oracle ATP
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum rows to return
        
        Returns:
            DataFrame with precipitation data
        """
        if not self.is_available():
            logger.warning("Oracle ATP not available")
            return pd.DataFrame()
        
        try:
            query = """
            SELECT 
                "DATE",
                precip,
                TO_CHAR("DATE", 'YYYY-MM') as year_month,
                EXTRACT(MONTH FROM "DATE") as month,
                EXTRACT(YEAR FROM "DATE") as year
            FROM CHIRPS_PRECIP_EXPORT
            """
            
            conditions = []
            if start_date:
                conditions.append(f"\"DATE\" >= TO_DATE('{start_date}', 'YYYY-MM-DD')")
            if end_date:
                conditions.append(f"\"DATE\" <= TO_DATE('{end_date}', 'YYYY-MM-DD')")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY \"DATE\" DESC FETCH FIRST {limit} ROWS ONLY"
            
            df = pd.read_sql(query, self.connection)
            logger.info(f"Retrieved {len(df)} rows from Oracle ATP")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch precipitation data: {e}")
            return pd.DataFrame()
    
    def get_latest_precipitation(self, days: int = 7) -> Dict:
        """
        Get latest precipitation data for the most recent N days in database
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            Dictionary with precipitation statistics
        """
        if not self.is_available():
            return {}
        
        try:
            # Get the most recent N days from the database (not relative to today)
            query = f"""
            SELECT 
                AVG(precip) as avg_precip,
                MAX(precip) as max_precip,
                MIN(precip) as min_precip,
                SUM(precip) as total_precip,
                COUNT(*) as days_count,
                MIN("DATE") as start_date,
                MAX("DATE") as end_date
            FROM (
                SELECT precip, "DATE"
                FROM CHIRPS_PRECIP_EXPORT
                ORDER BY "DATE" DESC
                FETCH FIRST {days} ROWS ONLY
            )
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            
            if row and row[0] is not None:
                return {
                    'avg_precip': float(row[0]),
                    'max_precip': float(row[1]) if row[1] else 0,
                    'min_precip': float(row[2]) if row[2] else 0,
                    'total_precip': float(row[3]) if row[3] else 0,
                    'days_count': int(row[4]) if row[4] else 0,
                    'period_days': days,
                    'start_date': row[5].isoformat() if row[5] else None,
                    'end_date': row[6].isoformat() if row[6] else None,
                    'data_source': 'Oracle Autonomous Database'
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get latest precipitation: {e}")
            return {}
    
    def get_monthly_summary(self, year: Optional[int] = None) -> List[Dict]:
        """
        Get monthly precipitation summary
        
        Args:
            year: Year to filter (optional)
        
        Returns:
            List of monthly summaries with proper formatting
        """
        if not self.is_available():
            return []
        
        try:
            query = """
            SELECT 
                TO_CHAR(\"DATE\", 'YYYY-MM') as year_month,
                EXTRACT(YEAR FROM \"DATE\") as year,
                EXTRACT(MONTH FROM \"DATE\") as month,
                COUNT(*) as days_count,
                AVG(precip) as avg_precip,
                MAX(precip) as max_precip,
                SUM(precip) as total_precip
            FROM CHIRPS_PRECIP_EXPORT
            """
            
            if year:
                query += f" WHERE EXTRACT(YEAR FROM \"DATE\") = {year}"
            
            query += """
            GROUP BY TO_CHAR(\"DATE\", 'YYYY-MM'), EXTRACT(YEAR FROM \"DATE\"), EXTRACT(MONTH FROM \"DATE\")
            ORDER BY year_month
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'year_month': row[0],
                    'year': int(row[1]),
                    'month': int(row[2]),
                    'days_count': int(row[3]),
                    'avg_precip': float(row[4]) if row[4] else 0,
                    'max_precip': float(row[5]) if row[5] else 0,
                    'total_precip': float(row[6]) if row[6] else 0
                })
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get monthly summary: {e}")
            return []
    
    def get_precipitation_for_location(
        self,
        lat: float,
        lon: float,
        date: datetime
    ) -> Dict:
        """
        Get precipitation data for a specific location and date
        Uses nearest available data point
        
        Args:
            lat: Latitude
            lon: Longitude
            date: Target date
        
        Returns:
            Dictionary with precipitation data
        """
        if not self.is_available():
            return self._get_fallback_data(lat, lon, date)
        
        try:
            # Get data for the specific date or nearest date
            query = """
            SELECT 
                \"DATE\",
                precip,
                ABS(\"DATE\" - TO_DATE(:target_date, 'YYYY-MM-DD')) as date_diff
            FROM CHIRPS_PRECIP_EXPORT
            WHERE \"DATE\" BETWEEN TO_DATE(:target_date, 'YYYY-MM-DD') - 7 
                          AND TO_DATE(:target_date, 'YYYY-MM-DD')
            ORDER BY date_diff
            FETCH FIRST 1 ROW ONLY
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, {
                'target_date': date.strftime('%Y-%m-%d')
            })
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return {
                    'date': row[0],
                    'precipitation': float(row[1]) if row[1] else 0,
                    'latitude': lat,
                    'longitude': lon,
                    'data_source': 'Oracle Autonomous Database',
                    'data_quality': 'high'
                }
            
            return self._get_fallback_data(lat, lon, date)
            
        except Exception as e:
            logger.error(f"Failed to get location data: {e}")
            return self._get_fallback_data(lat, lon, date)
    
    def _get_fallback_data(self, lat: float, lon: float, date: datetime) -> Dict:
        """Fallback data when Oracle ATP is unavailable"""
        return {
            'date': date,
            'precipitation': 0,
            'latitude': lat,
            'longitude': lon,
            'data_source': 'Fallback',
            'data_quality': 'low'
        }
    
    def close(self):
        """Close Oracle ATP connection"""
        if self.connection:
            self.connection.close()
            logger.info("Oracle ATP connection closed")


# Global instance
_oracle_service: Optional[OracleDataService] = None


def get_oracle_data_service() -> OracleDataService:
    """Get or create Oracle data service singleton"""
    global _oracle_service
    if _oracle_service is None:
        _oracle_service = OracleDataService()
    return _oracle_service
