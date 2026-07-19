# ==============================================================================
# trust_ledger.py — CHRONOS Trust Ledger & Audit System
# ==============================================================================
# Maintains a transparent, persistent audit ledger of all node actions,
# tool executions, security gates, and verifier verdicts across all profiles.
# ==============================================================================

import os
import json
import sqlite3
import time
from datetime import datetime

SECURITY_DIR = "CHRONOS_SECURITY"
DB_PATH = os.path.join(SECURITY_DIR, "trust_ledger.db")

def _init_db():
 """Initializes the Trust Ledger SQLite database table if not present."""
 os.makedirs(SECURITY_DIR, exist_ok=True)
 conn = sqlite3.connect(DB_PATH)
 cursor = conn.cursor()
 cursor.execute("""
  CREATE TABLE IF NOT EXISTS trust_ledger (
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   timestamp TEXT NOT NULL,
   profile TEXT NOT NULL,
   event_type TEXT NOT NULL,
   action TEXT NOT NULL,
   status TEXT NOT NULL,
   details TEXT,
   model_used TEXT
  )
 """)
 conn.commit()
 conn.close()

# Ensure database is initialized on import
_init_db()

def log_event(event_type: str, action: str, status: str, details: dict | str = None, profile: str = "personal", model_used: str = "N/A") -> int:
 """
 Logs an audit event to the persistent Trust Ledger.
 Returns the logged event ID.
 """
 try:
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  
  timestamp = datetime.now().isoformat()
  details_json = json.dumps(details) if isinstance(details, (dict, list)) else str(details or "")
  
  cursor.execute("""
   INSERT INTO trust_ledger (timestamp, profile, event_type, action, status, details, model_used)
   VALUES (?, ?, ?, ?, ?, ?, ?)
  """, (timestamp, profile, event_type, action, status, details_json, model_used))
  
  conn.commit()
  event_id = cursor.lastrowid
  conn.close()
  
  print(f" [Trust Ledger]: Logged event #{event_id} [{event_type}] '{action}' ({status})")
  return event_id
 except Exception as e:
  print(f"️ [Trust Ledger Error]: Failed to log event: {e}")
  return -1

def get_recent_logs(limit: int = 50, profile: str = None) -> list:
 """Retrieves recent audit events from the Trust Ledger."""
 try:
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  
  if profile:
   cursor.execute("""
    SELECT id, timestamp, profile, event_type, action, status, details, model_used
    FROM trust_ledger WHERE profile = ? ORDER BY id DESC LIMIT ?
   """, (profile, limit))
  else:
   cursor.execute("""
    SELECT id, timestamp, profile, event_type, action, status, details, model_used
    FROM trust_ledger ORDER BY id DESC LIMIT ?
   """, (limit,))
   
  rows = cursor.fetchall()
  conn.close()
  
  logs = []
  for r in rows:
   details_parsed = r[6]
   try:
    details_parsed = json.loads(r[6])
   except Exception:
    pass
    
   logs.append({
    "id": r[0],
    "timestamp": r[1],
    "profile": r[2],
    "event_type": r[3],
    "action": r[4],
    "status": r[5],
    "details": details_parsed,
    "model_used": r[7]
   })
  return logs
 except Exception as e:
  print(f"️ [Trust Ledger Error]: Failed to fetch logs: {e}")
  return []

def get_audit_summary() -> dict:
 """Returns total counts and statistics for security audit reporting."""
 try:
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  
  cursor.execute("SELECT COUNT(*) FROM trust_ledger")
  total_events = cursor.fetchone()[0]
  
  cursor.execute("SELECT COUNT(*) FROM trust_ledger WHERE status = 'APPROVED'")
  approved_count = cursor.fetchone()[0]
  
  cursor.execute("SELECT COUNT(*) FROM trust_ledger WHERE status = 'DENIED'")
  denied_count = cursor.fetchone()[0]
  
  cursor.execute("SELECT COUNT(*) FROM trust_ledger WHERE event_type = 'PERMISSION_GATE'")
  permission_gates = cursor.fetchone()[0]
  
  conn.close()
  
  return {
   "total_events": total_events,
   "approved": approved_count,
   "denied": denied_count,
   "permission_gate_requests": permission_gates,
  }
 except Exception as e:
  print(f"️ [Trust Ledger Error]: Failed to fetch summary: {e}")
  return {"total_events": 0, "approved": 0, "denied": 0, "permission_gate_requests": 0}
