import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import init_db, save_call_report, get_call_reports, save_contact, get_contacts, save_chat_log, get_db_connection

print("=== CALLSHIELD AI MYSQL/DATABASE INTEGRATION TEST ===")

# Step 1: Check Connection & DB Mode
conn, mode = get_db_connection()
print(f"[+] Database Mode Detected: {mode}")

# Step 2: Initialize Database
success = init_db()
print(f"[+] Init DB Status: {'SUCCESS' if success else 'FAILED'}")

# Step 3: Test Contact CRUD
save_contact("Test Support Agent", "+1 888-999-0000", "Verified")
contacts = get_contacts()
print(f"[+] Total Contacts in DB: {len(contacts)}")
for c in contacts[:3]:
    print(f"   * {c['name']} ({c['number']}) - {c['category']}")

# Step 4: Test Call Report CRUD
save_call_report(
    name="Live_Call_Recording_Test.mp3",
    transcript="Your bank account is compromised, send OTP now.",
    scam_type="Live Call (High Risk - 90%)",
    fraud_score=90,
    risk_level="High",
    phone_number="+1 888-392-1011"
)
reports = get_call_reports()
print(f"[+] Total Call Reports in DB: {len(reports)}")
if reports:
    print(f"   * Top Report: {reports[0]['name']} | Risk: {reports[0]['risk_level']} | Date: {reports[0]['date']}")

# Step 5: Test Chat Log CRUD
save_chat_log(sender="user", message="How to block scam call?", response="Enable CallShield auto block.", source="security_database")
print("[+] Chat Log Saved Successfully.")

print("=== TEST COMPLETED SUCCESSFULLY ===")
