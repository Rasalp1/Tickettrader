#BERÄKNA RATION MELLAN TRADESEN OCH LAGRA DEN DATAN

import sqlite3
import itertools
from collections import defaultdict
import statistics # For calculating the mean
from tradestorer import *

TRADE_DATABASE_NAME = 'ticket_trades.db'
RATIO_DATABASE_NAME = "ticket_trades_ratios.db"

# --- Ratio Calculation Function ---
def calculate_relative_values():
    """
    Calculates the relative value between ticket types based on the total
    quantities exchanged in historical trades involving only those two types.
    This provides a quantity-weighted average ratio.

    Returns:
        dict: A dictionary where keys are tuples (Type A, Type B) and
              values are dictionaries containing 'average_ratio' (Value A / Value B)
              and 'trade_count'. Returns None if an error occurs.
              Returns an empty dict if no valid trades are found.
    """
    conn = None
    relative_values = {}
    try:
        conn = sqlite3.connect(TRADE_DATABASE_NAME)
        cursor = conn.cursor()
        # Fetch trades, ensuring quantities are positive and types are valid
        cursor.execute("""
            SELECT offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type
            FROM ticket_trades
            WHERE offered_quantity > 0 AND requested_quantity > 0
              AND offered_ticket_type IS NOT NULL AND offered_ticket_type != ''
              AND requested_ticket_type IS NOT NULL AND requested_ticket_type != ''
        """)
        all_trades = cursor.fetchall()

        if not all_trades:
            print("No valid trade data found in the database.")
            return {}

        # --- NEW LOGIC START ---

        # Dictionary to store aggregated stats for each PAIR of ticket types.
        # We use a canonical key (sorted tuple) to treat (A, B) and (B, A) trades
        # as affecting the same underlying pair relationship.
        # Stores total quantities exchanged FOR THAT PAIR ONLY.
        pair_exchange_stats = defaultdict(lambda: {
            'total_type1_exchanged': 0, # Total quantity of the first type in the sorted pair key
            'total_type2_exchanged': 0, # Total quantity of the second type in the sorted pair key
            'trade_count': 0            # Number of direct trades between these two types
        })

        unique_types = set() # Still need to know all types involved

        # 1. Aggregate exchange quantities for each pair
        for oq, ot, rq, rt in all_trades:
            # Clean types for consistency
            ot_clean = ot.strip().upper() if ot else None
            rt_clean = rt.strip().upper() if rt else None

            if not ot_clean or not rt_clean or ot_clean == rt_clean:
                # Skip trades with invalid types or trades of a type for itself
                if ot_clean == rt_clean and ot_clean is not None:
                    print(f"Warning: Skipping self-trade: {oq} {ot_clean} -> {rq} {rt_clean}")
                else:
                    print(f"Warning: Skipping trade with invalid types: {oq} {ot} -> {rq} {rt}")
                continue

            # Add types to the set for later iteration if needed
            unique_types.add(ot_clean)
            unique_types.add(rt_clean)

            # Create canonical key (sorted tuple) for the pair
            pair_key = tuple(sorted((ot_clean, rt_clean)))
            type1, type2 = pair_key # type1 is alphabetically first

            # Add quantities to the correct bucket based on the canonical key
            if ot_clean == type1: # Trade was Type1 offered for Type2 requested (Type1 -> Type2)
                pair_exchange_stats[pair_key]['total_type1_exchanged'] += oq
                pair_exchange_stats[pair_key]['total_type2_exchanged'] += rq
            else: # Trade was Type2 offered for Type1 requested (Type2 -> Type1)
                pair_exchange_stats[pair_key]['total_type1_exchanged'] += rq # rq is Type1 here
                pair_exchange_stats[pair_key]['total_type2_exchanged'] += oq # oq is Type2 here

            pair_exchange_stats[pair_key]['trade_count'] += 1

        # 2. Calculate final ratios from aggregated stats
        relative_values = {}
        processed_pairs = set() # To avoid adding inverse if already processed

        # Iterate through the unique types to ensure all pairs are considered,
        # even if one direction of trade never occurred but stats were added via the canonical key.
        unique_types_list = sorted(list(unique_types))
        for type_a, type_b in itertools.combinations(unique_types_list, 2):
             # Use the canonical key to fetch stats
            pair_key = tuple(sorted((type_a, type_b)))
            type1, type2 = pair_key

            if pair_key in pair_exchange_stats:
                stats = pair_exchange_stats[pair_key]
                total_type1 = stats['total_type1_exchanged']
                total_type2 = stats['total_type2_exchanged']
                trade_count = stats['trade_count']

                # Determine which total corresponds to type_a and type_b
                total_a = total_type1 if type_a == type1 else total_type2
                total_b = total_type2 if type_b == type2 else total_type1 # Or simply the other one

                # Calculate Value(A) / Value(B) => How many B per A = Total B / Total A
                if total_a > 0:
                    ratio_a_div_b = total_b / total_a
                    relative_values[(type_a, type_b)] = {
                        'average_ratio': ratio_a_div_b,
                        'trade_count': trade_count
                    }
                else:
                    # Cannot determine ratio if no A was ever exchanged for B
                     relative_values[(type_a, type_b)] = {
                        'average_ratio': None, # Or float('inf') or 0 depending on desired handling
                        'trade_count': trade_count
                    }

                # Calculate Value(B) / Value(A) => How many A per B = Total A / Total B
                if total_b > 0:
                    ratio_b_div_a = total_a / total_b
                    relative_values[(type_b, type_a)] = {
                        'average_ratio': ratio_b_div_a,
                        'trade_count': trade_count
                    }
                else:
                    # Cannot determine ratio if no B was ever exchanged for A
                     relative_values[(type_b, type_a)] = {
                        'average_ratio': None, # Or float('inf') or 0
                        'trade_count': trade_count
                    }

        # --- NEW LOGIC END ---

        return relative_values

    except sqlite3.Error as e:
        print(f"Database error during calculation in '{TRADE_DATABASE_NAME}': {e}")
        return None # Indicate error
    except Exception as e:
        print(f"Error calculating relative values: {e}")
        return None # Indicate error
    finally:
        if conn:
            conn.close()


def create_relative_values_table():
    conn = sqlite3.connect(RATIO_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticket_trades_ratios (
            type_a TEXT,
            type_b TEXT,
            average_ratio REAL,
            trade_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (type_a, type_b)
        )
    ''')
    conn.commit()
    conn.close()


def save_relative_values(relative_values):
    if not relative_values:  # Check for empty dict
        print("No relative values provided to save.")
        return
    try:
        conn = sqlite3.connect(RATIO_DATABASE_NAME)
        cursor = conn.cursor()

        # Prepare data for executemany
        data_to_upsert = []
        for pair, stats in relative_values.items():
            type_a, type_b = pair
            average_ratio = round(stats.get('average_ratio'),1)
            trade_count = stats.get('trade_count')

            # Basic validation - skip if data seems incomplete
            if type_a is None or type_b is None or average_ratio is None or trade_count is None:
                print(f"Warning: Skipping incomplete data for pair {pair}")
                continue

            data_to_upsert.append((type_a, type_b, float(average_ratio), int(trade_count)))  # Ensure types

        if not data_to_upsert:
            print("No valid data formatted for saving.")
            return

        # SQL statement for UPSERT (using ON CONFLICT)
        sql_upsert = '''
            INSERT INTO ticket_trades_ratios (type_a, type_b, average_ratio, trade_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(type_a, type_b) DO UPDATE SET
                average_ratio = excluded.average_ratio,
                trade_count = excluded.trade_count,
                timestamp = CURRENT_TIMESTAMP
        '''
        cursor.executemany(sql_upsert, data_to_upsert)
        conn.commit()
        print(f"Successfully saved/updated {len(data_to_upsert)} ratio entries.")

    except sqlite3.Error as e:
        print(f"Database error during save/update: {e}")
        if conn:
            conn.rollback()  # Rollback changes on error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def remove_entry(type_a, type_b):
    """
    Removes a specific entry from the ticket_trades_ratios table based on type_a and type_b.

    Args:
        type_a (str): The req type of the entry to remove.
        type_b (str): The off type of the entry to remove.
    """
    conn = None
    try:
        conn = sqlite3.connect(RATIO_DATABASE_NAME)
        cursor = conn.cursor()

        # SQL statement to delete the entry
        sql_delete = '''
            DELETE FROM ticket_trades_ratios
            WHERE type_a = ? AND type_b = ?
        '''
        cursor.execute(sql_delete, (type_a, type_b))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Successfully removed entry: (type_a={type_a}, type_b={type_b})")
        else:
            print(f"No entry found with type_a='{type_a}' and type_b='{type_b}'.")

    except sqlite3.Error as e:
        print(f"Database error during deletion: {e}")
        if conn:
            conn.rollback()  # Rollback changes on error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def viewdb():
    conn = sqlite3.connect(RATIO_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ticket_trades_ratios")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    create_relative_values_table()
    save_relative_values(calculate_relative_values())
    viewdb()
