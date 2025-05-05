#LAGRA DE INLÄSTA TRADESEN

import sqlite3

# Database interaction
TRADE_DATABASE_NAME = 'ticket_trades.db'

def create_trades_table():
    conn = sqlite3.connect(TRADE_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_trades (
            offered_quantity INTEGER,
            offered_ticket_type TEXT,
            requested_quantity INTEGER,
            requested_ticket_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_trade_entry(offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type):
    conn = sqlite3.connect(TRADE_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ticket_trades (offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type)
        VALUES (?, ?, ?, ?)
    """, (offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type))
    conn.commit()
    conn.close()

def remove_trade_entry(ticket_type):
    """
    Removes all entries from the ticket_trades table where either
    offered_ticket_type or requested_ticket_type is 'type'.
    """
    conn = None
    try:
        conn = sqlite3.connect(TRADE_DATABASE_NAME)
        cursor = conn.cursor()

        # SQL statement to delete entries
        sql_delete = """
            DELETE FROM ticket_trades
            WHERE offered_ticket_type = ? OR requested_ticket_type = ?
        """
        cursor.execute(sql_delete, (ticket_type, ticket_type))  # Use parameter binding
        conn.commit()

        print(f"Removed {cursor.rowcount} entries containing '{ticket_type}'.")

    except sqlite3.Error as e:
        print(f"Database error during deletion: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def viewdb():
    conn = sqlite3.connect(TRADE_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ticket_trades")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()


create_trades_table() #Creates table if it doesn't already exist

if __name__ == "__main__":
    #add_trade_entry(2, "NSA", 3, "ÖG")
    remove_trade_entry("Sydskånska")
    viewdb()

