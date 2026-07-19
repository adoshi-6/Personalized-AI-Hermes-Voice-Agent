# ==============================================================================
# crm_engine.py — CHRONOS Lead Management & CRM Module
# ==============================================================================
# Provides a clean SQLite-backed CRM and appointment database for both
# Business and Personal profiles.
# ==============================================================================

import os
import json
import sqlite3
from datetime import datetime

SECURITY_DIR = "CHRONOS_SECURITY"
CRM_DB_PATH = os.path.join(SECURITY_DIR, "crm_database.db")

def _init_crm_db():
  """Initializes the CRM SQLite database tables if not present."""
  os.makedirs(SECURITY_DIR, exist_ok=True)
  conn = sqlite3.connect(CRM_DB_PATH)
  cursor = conn.cursor()
  
  # Table 1: Leads
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT,
      phone TEXT,
      status TEXT DEFAULT 'NEW',
      notes TEXT,
      created_at TEXT NOT NULL,
      last_contact TEXT
    )
  """)
  
  # Table 2: Appointments
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      lead_id INTEGER,
      title TEXT NOT NULL,
      start_time TEXT NOT NULL,
      end_time TEXT,
      status TEXT DEFAULT 'SCHEDULED',
      notes TEXT,
      FOREIGN KEY (lead_id) REFERENCES leads (id)
    )
  """)
  
  conn.commit()
  conn.close()

# Initialize CRM tables on import
_init_crm_db()

def add_lead(name: str, email: str = "", phone: str = "", notes: str = "") -> dict:
  """Adds a new lead to the CRM database."""
  try:
    conn = sqlite3.connect(CRM_DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute("""
      INSERT INTO leads (name, email, phone, status, notes, created_at, last_contact)
      VALUES (?, ?, ?, 'NEW', ?, ?, ?)
    """, (name, email, phone, notes, now, now))
    
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f" [CRM]: Added new lead #{lead_id} '{name}' ({email})")
    return {"status": "success", "lead_id": lead_id, "name": name}
  except Exception as e:
    print(f"️ [CRM Error]: Failed to add lead: {e}")
    return {"status": "error", "message": str(e)}

def get_leads(status_filter: str = None) -> list:
  """Retrieves leads from the CRM database."""
  try:
    conn = sqlite3.connect(CRM_DB_PATH)
    cursor = conn.cursor()
    
    if status_filter:
      cursor.execute("""
        SELECT id, name, email, phone, status, notes, created_at, last_contact
        FROM leads WHERE status = ? ORDER BY id DESC
      """, (status_filter,))
    else:
      cursor.execute("""
        SELECT id, name, email, phone, status, notes, created_at, last_contact
        FROM leads ORDER BY id DESC
      """)
      
    rows = cursor.fetchall()
    conn.close()
    
    leads = []
    for r in rows:
      leads.append({
        "id": r[0],
        "name": r[1],
        "email": r[2],
        "phone": r[3],
        "status": r[4],
        "notes": r[5],
        "created_at": r[6],
        "last_contact": r[7]
      })
    return leads
  except Exception as e:
    print(f"️ [CRM Error]: Failed to fetch leads: {e}")
    return []

def update_lead_status(lead_id: int, new_status: str, notes_append: str = "") -> dict:
  """Updates the status and notes of a lead."""
  try:
    conn = sqlite3.connect(CRM_DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    if notes_append:
      cursor.execute("""
        UPDATE leads
        SET status = ?, notes = notes || '\n' || ?, last_contact = ?
        WHERE id = ?
      """, (new_status, notes_append, now, lead_id))
    else:
      cursor.execute("""
        UPDATE leads
        SET status = ?, last_contact = ?
        WHERE id = ?
      """, (new_status, now, lead_id))
      
    conn.commit()
    conn.close()
    return {"status": "success", "lead_id": lead_id, "new_status": new_status}
  except Exception as e:
    return {"status": "error", "message": str(e)}

def schedule_appointment(title: str, start_time: str, lead_id: int = None, notes: str = "") -> dict:
  """Schedules a business appointment in the CRM database."""
  try:
    conn = sqlite3.connect(CRM_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
      INSERT INTO appointments (lead_id, title, start_time, status, notes)
      VALUES (?, ?, ?, 'SCHEDULED', ?)
    """, (lead_id, title, start_time, notes))
    
    appt_id = cursor.lastrowid
    
    if lead_id:
      now = datetime.now().isoformat()
      cursor.execute("UPDATE leads SET status = 'APPOINTMENT_SET', last_contact = ? WHERE id = ?", (now, lead_id))
      
    conn.commit()
    conn.close()
    
    print(f" [CRM]: Scheduled appointment #{appt_id} '{title}' at {start_time}")
    return {"status": "success", "appointment_id": appt_id, "title": title, "start_time": start_time}
  except Exception as e:
    return {"status": "error", "message": str(e)}

def get_upcoming_appointments() -> list:
  """Retrieves upcoming appointments from the database."""
  try:
    conn = sqlite3.connect(CRM_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
      SELECT a.id, a.title, a.start_time, a.status, a.notes, l.name, l.email
      FROM appointments a
      LEFT JOIN leads l ON a.lead_id = l.id
      ORDER BY a.start_time ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    appts = []
    for r in rows:
      appts.append({
        "id": r[0],
        "title": r[1],
        "start_time": r[2],
        "status": r[3],
        "notes": r[4],
        "lead_name": r[5] or "N/A",
        "lead_email": r[6] or "N/A"
      })
    return appts
  except Exception as e:
    print(f"️ [CRM Error]: Failed to fetch appointments: {e}")
    return []
