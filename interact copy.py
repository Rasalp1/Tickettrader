#INTERAGERA MED RATIOSARNA 

import sqlite3
from ratiocalc import *

RATIO_DATABASE_NAME = "ticket_trades_ratios.db"

def fetch_relative_values():
    conn = sqlite3.connect(RATIO_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT type_a, type_b, average_ratio, trade_count
        FROM ticket_trades_ratios
    ''')
    results = cursor.fetchall()
    conn.close()

    # Transform into a similar structure as before for easier use
    relative_values = {}
    for type_a, type_b, average_ratio, trade_count in results:
        relative_values[(type_a, type_b)] = {
            'average_ratio': average_ratio,
            'trade_count': trade_count
        }
    return relative_values

def display_relationships():
    relative_values = fetch_relative_values()
    if relative_values is not None:
        if len(relative_values) == 0:
            print("No relative values stored in the database.")
        else:
            sorted_pairs = sorted(relative_values.keys()) # Sort for readability
            for pair in sorted_pairs:
                type_a, type_b = pair
                stats = relative_values[pair]
                ratio = round(stats['average_ratio'],1)
                count = stats['trade_count']
                #print(f"- {type_a} -> {type_b}: {ratio} (based on {count} trades)")
                print(f" - 1 {type_a} is worth {ratio} {type_b} (based on {count} trades)")

# Check a hypothetical trade
def hypotrade(off_t: str, off_a: int, req_t: str, req_a: int):
    relative_values = fetch_relative_values()
    off_req_key = (off_t, req_t)
    avg_ratio = relative_values[off_req_key]['average_ratio']
    trade_ratio = req_a / off_a # How many requested per offered in this trade

    if trade_ratio < avg_ratio:
        status = "underpay"
        message = f"  A trade of {off_a} {off_t} for {req_a} {req_t} ({trade_ratio} {req_t}/{off_t}) looks like an 'underpay' compared to the average of ({avg_ratio} {req_t}/{off_t})."
    elif trade_ratio > avg_ratio:
        status = "overpay"
        message = f"  A trade of {off_a} {off_t} for {req_a} {req_t} ({trade_ratio} {req_t}/{off_t}) looks like an 'overpay' compared to the average ({avg_ratio} {req_t}/{off_t})."
    else:
        status = "fair"
        message = f"  A trade of {off_a} {off_t} for {req_a} {req_t} ({trade_ratio} {req_t}/{off_t}) seems fair based on the average."
    info_dict = {
        "trade_details": {
            "offered_type": off_t,
            "offered_amount": off_a,
            "requested_type": req_t,
            "requested_amount": req_a,
        },
        "analysis": {
            "status": status,
            "message": message,
            "your_ratio": round(trade_ratio, 1),
            "average_ratio": round(avg_ratio, 1),
            "ratio_unit": f"{req_t}_per_{off_t}",
        }
    }
    return info_dict

def oneofthisequals(base_type: str, base_quantity: float):
    """
    Calculates the equivalent value of other ticket types based on a given quantity of a base type.

    Returns:
        dict: A dictionary where keys are other ticket types and values are
              their calculated equivalent quantities. Returns an empty dict if
              no relationships can be found or data is missing.
    """
    relative_values = fetch_relative_values()
    if relative_values is None or not relative_values:
        print("Cannot calculate relative values: No relationship data available.")
        return {}
    
    calculation_details = []

    equivalents = {}
    all_types = set()
    for type_a, type_b in relative_values.keys():
        all_types.add(type_a)
        all_types.add(type_b)

    if base_type not in all_types:
        print(f"Warning: Base type '{base_type}' not found in any recorded relationships.")
        return {}

    print(f"\n--- Calculating Equivalents for {base_quantity} {base_type} ---")

    for other_type in all_types:
        if other_type == base_type:
            continue # Skip calculating value relative to itself

        equivalent_quantity = None

        # Try direct relationship: base_type -> other_type
        direct_key = (base_type, other_type)
        if direct_key in relative_values:
            ratio = relative_values[direct_key]['average_ratio']
            equivalent_quantity = base_quantity * ratio
            trade_count = relative_values[direct_key]['trade_count']
            #print(f"1 {base_type} = {ratio} {other_type}. ", end="") # Debug / Info line

        # Store the result if found
        if equivalent_quantity is not None:
            equivalents[other_type] = round(equivalent_quantity, 2)
            #print(f"-> {base_quantity} {base_type} is worth approx. {equivalents[other_type]} {other_type}")

        else:
            equivalents[other_type] = None
            trade_count = 0
            ratio = 0

            print(f" No relationship found to calculate value for {other_type}.")

        detail = {
        "target_type": other_type,
        "equivalent_quantity": None,
        "trade_count_for_relation": trade_count
    }
        if equivalent_quantity is not None:    
            rounded_quantity = round(equivalent_quantity, 2)
            equivalents[other_type] = rounded_quantity # Round for cleaner display
            detail["equivalent_quantity"] = rounded_quantity

        if ratio is not None:
            detail["effective_ratio"] = round(ratio, 1) # (target_type per base_type)

            calculation_details.append(detail)
            
    if not equivalents:
        print(f"Could not determine relative values for any other ticket type based on {base_type}.")



    # --- Format Response ---
    response = {
        "base_type": base_type,
        "base_quantity": base_quantity,
        "equivalents": equivalents,
        "calculation_details": calculation_details
    }

    if not equivalents:
        response["message"] = f"Could not determine relative values for any other ticket type based on {base_type} using available data."

    return response

if __name__ == "__main__":
    #display_relationships()
    #print(hypotrade("NSA", 3, "ÖG", 4))
    print(oneofthisequals("NSA", 4))