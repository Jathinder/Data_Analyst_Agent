import sqlite3
conn = sqlite3.connect("chinook.db")

print("Tracks > 5 min:", conn.execute("SELECT COUNT(*) FROM Track WHERE Milliseconds > 300000").fetchone())
print("Invoices for CustomerId 1:", conn.execute("SELECT COUNT(*) FROM Invoice WHERE CustomerId = 1").fetchone())
print("Total revenue:", conn.execute("SELECT ROUND(SUM(Total), 2) FROM Invoice").fetchone())
print("Avg unit price:", conn.execute("SELECT ROUND(AVG(UnitPrice), 2) FROM Track").fetchone())
