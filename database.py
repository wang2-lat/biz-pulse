import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

class Database:
    def __init__(self, db_path="biz_pulse.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                stage TEXT DEFAULT 'lead',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                amount REAL,
                stage TEXT DEFAULT 'proposal',
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                notes TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER,
                description TEXT NOT NULL,
                assignee TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_customer(self, name, email, phone, stage):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name, email, phone, stage) VALUES (?, ?, ?, ?)",
            (name, email, phone, stage)
        )
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return customer_id
    
    def get_customers(self, status_filter="all"):
        conn = self.get_connection()
        cursor = conn.cursor()
        if status_filter == "all":
            cursor.execute("SELECT id, name, email, phone, stage, status FROM customers")
        else:
            cursor.execute(
                "SELECT id, name, email, phone, stage, status FROM customers WHERE status = ?",
                (status_filter,)
            )
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    def update_customer(self, customer_id, stage, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        if stage:
            cursor.execute(
                "UPDATE customers SET stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (stage, customer_id)
            )
        if status:
            cursor.execute(
                "UPDATE customers SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, customer_id)
            )
        conn.commit()
        conn.close()
    
    def add_deal(self, customer_id, amount, stage):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO deals (customer_id, amount, stage) VALUES (?, ?, ?)",
            (customer_id, amount, stage)
        )
        deal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return deal_id
    
    def get_deals(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id, c.name, d.amount, d.stage, d.status
            FROM deals d
            JOIN customers c ON d.customer_id = c.id
        """)
        deals = cursor.fetchall()
        conn.close()
        return deals
    
    def update_deal_status(self, deal_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE deals SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, deal_id)
        )
        conn.commit()
        conn.close()
    
    def get_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Won this month
        first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM deals WHERE status = 'won' AND updated_at >= ?",
            (first_day,)
        )
        won_this_month = cursor.fetchone()[0]
        
        # Active deals
        cursor.execute("SELECT COUNT(*) FROM deals WHERE status = 'active'")
        active_deals = cursor.fetchone()[0]
        
        # At risk customers (no update in 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM customers WHERE status = 'active' AND updated_at < ?",
            (thirty_days_ago,)
        )
        at_risk = cursor.fetchone()[0]
        
        # Total revenue
        cursor.execute("SELECT SUM(amount) FROM deals WHERE status = 'won'")
        total_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "won_this_month": won_this_month,
            "active_deals": active_deals,
            "at_risk": at_risk,
            "total_revenue": total_revenue
        }
    
    def get_funnel(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stage, COUNT(*) FROM customers WHERE status = 'active' GROUP BY stage"
        )
        funnel = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return funnel
    
    def add_meeting(self, title, notes):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO meetings (title, notes) VALUES (?, ?)",
            (title, notes)
        )
        meeting_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return meeting_id
    
    def get_meetings(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, date, notes FROM meetings ORDER BY date DESC")
        meetings = cursor.fetchall()
        conn.close()
        return meetings
    
    def add_task(self, description, assignee, meeting_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (description, assignee, meeting_id) VALUES (?, ?, ?)",
            (description, assignee, meeting_id)
        )
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def get_tasks(self, status_filter="pending"):
        conn = self.get_connection()
        cursor = conn.cursor()
        if status_filter == "all":
            cursor.execute(
                "SELECT id, description, assignee, status, created_at FROM tasks ORDER BY created_at DESC"
            )
        else:
            cursor.execute(
                "SELECT id, description, assignee, status, created_at FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status_filter,)
            )
        tasks = cursor.fetchall()
        conn.close()
        return tasks
    
    def update_task_status(self, task_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, task_id))
        conn.commit()
        conn.close()
