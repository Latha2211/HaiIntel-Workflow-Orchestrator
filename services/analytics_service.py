"""
Analytics service for tracking and reporting customer issues
"""

import sqlite3
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalyticsService:
    """Service for analytics and reporting"""
    
    def __init__(self):
        self.db_path = settings.ANALYTICS_DB_PATH
        self.enabled = settings.ANALYTICS_ENABLED
        
        if self.enabled:
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create issues table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT UNIQUE NOT NULL,
                    customer_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    resolution_time INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON issues(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON issues(sentiment)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON issues(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_channel ON issues(channel)')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Analytics database initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing database: {str(e)}")
    
    async def track_issue(
        self,
        ticket_id: str,
        customer_id: str,
        category: str,
        sentiment: str,
        priority: str,
        channel: str,
        resolution_time: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track a new issue"""
        if not self.enabled:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute('''
                INSERT INTO issues 
                (ticket_id, customer_id, category, sentiment, priority, channel, resolution_time, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (ticket_id, customer_id, category, sentiment, priority, channel, resolution_time, metadata_json))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Issue {ticket_id} tracked in analytics")
            
        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Issue {ticket_id} already tracked")
        except Exception as e:
            logger.error(f"❌ Error tracking issue: {str(e)}")
    
    async def update_resolution(
        self,
        ticket_id: str,
        resolution_time: int
    ):
        """Update resolution time for an issue"""
        if not self.enabled:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE issues 
                SET resolution_time = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE ticket_id = ?
            ''', (resolution_time, ticket_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Resolution time updated for {ticket_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating resolution: {str(e)}")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard analytics"""
        if not self.enabled:
            return {"error": "Analytics disabled"}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total issues
            cursor.execute('SELECT COUNT(*) FROM issues')
            total_issues = cursor.fetchone()[0]
            
            # Issues by category
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM issues 
                GROUP BY category 
                ORDER BY count DESC
            ''')
            by_category = dict(cursor.fetchall())
            
            # Issues by sentiment
            cursor.execute('''
                SELECT sentiment, COUNT(*) as count 
                FROM issues 
                GROUP BY sentiment
            ''')
            by_sentiment = dict(cursor.fetchall())
            
            # Issues by channel
            cursor.execute('''
                SELECT channel, COUNT(*) as count 
                FROM issues 
                GROUP BY channel
            ''')
            by_channel = dict(cursor.fetchall())
            
            # Issues by priority
            cursor.execute('''
                SELECT priority, COUNT(*) as count 
                FROM issues 
                GROUP BY priority
            ''')
            by_priority = dict(cursor.fetchall())
            
            # Average resolution time
            cursor.execute('''
                SELECT AVG(resolution_time) 
                FROM issues 
                WHERE resolution_time IS NOT NULL
            ''')
            avg_resolution = cursor.fetchone()[0] or 0
            
            # Issues last 24 hours
            cursor.execute('''
                SELECT COUNT(*) 
                FROM issues 
                WHERE created_at >= datetime('now', '-1 day')
            ''')
            last_24h = cursor.fetchone()[0]
            
            # Issues last 7 days
            cursor.execute('''
                SELECT COUNT(*) 
                FROM issues 
                WHERE created_at >= datetime('now', '-7 days')
            ''')
            last_7d = cursor.fetchone()[0]
            
            # Resolution rate
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) 
                FROM issues
            ''')
            resolution_rate = cursor.fetchone()[0] or 0
            
            # Trend data (last 7 days)
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count
                FROM issues
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            ''')
            trend_data = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            dashboard = {
                "summary": {
                    "total_issues": total_issues,
                    "last_24h": last_24h,
                    "last_7d": last_7d,
                    "avg_resolution_hours": round(avg_resolution / 3600, 2) if avg_resolution else 0,
                    "resolution_rate": round(resolution_rate, 2)
                },
                "by_category": by_category,
                "by_sentiment": by_sentiment,
                "by_channel": by_channel,
                "by_priority": by_priority,
                "trend": trend_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            logger.info("✅ Dashboard data generated")
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Error generating dashboard: {str(e)}")
            return {"error": str(e)}
    
    async def get_category_insights(self) -> Dict[str, Any]:
        """Get detailed insights by category"""
        if not self.enabled:
            return {"error": "Analytics disabled"}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    category,
                    COUNT(*) as total,
                    AVG(CASE WHEN resolution_time IS NOT NULL THEN resolution_time END) as avg_resolution,
                    COUNT(CASE WHEN sentiment = 'negative' OR sentiment = 'very_negative' THEN 1 END) * 100.0 / COUNT(*) as negative_rate
                FROM issues
                GROUP BY category
                ORDER BY total DESC
            ''')
            
            insights = []
            for row in cursor.fetchall():
                insights.append({
                    "category": row[0],
                    "total": row[1],
                    "avg_resolution_hours": round(row[2] / 3600, 2) if row[2] else 0,
                    "negative_sentiment_rate": round(row[3], 2)
                })
            
            conn.close()
            return {"insights": insights}
            
        except Exception as e:
            logger.error(f"❌ Error getting category insights: {str(e)}")
            return {"error": str(e)}
    
    async def export_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Export analytics data"""
        if not self.enabled:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM issues WHERE 1=1'
            params = []
            
            if start_date:
                query += ' AND created_at >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND created_at <= ?'
                params.append(end_date)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            
            conn.close()
            logger.info(f"✅ Exported {len(data)} records")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error exporting data: {str(e)}")
            return []
