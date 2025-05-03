from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3 # Keep for catching potential DB errors at API layer if needed
from interact import *


# --- Flask App Setup ---
app = Flask(__name__)
# Enable CORS for all domains on all routes.
CORS(app)


# --- Helper for Handling Errors Returned by Logic Functions ---
def handle_logic_error(result):
    """Checks result dict from logic functions for error key."""
    if isinstance(result, dict) and "error" in result:
        error_type = result.get("error", "unknown_error")
        message = result.get("message", "An unspecified error occurred.")
        status_code = 500 # Default Internal Server Error

        # Map specific error types from the logic functions to HTTP status codes
        if error_type == "database_not_found":
            status_code = 503 # Service Unavailable (can't reach DB)
        elif error_type == "database_error":
            status_code = 500
        elif error_type == "relation_not_found" or error_type == "type_not_found":
            status_code = 404 # Not Found
        elif error_type == "calculation_error" or error_type == "invalid_ratio":
             status_code = 500 # Internal error if calculations fail
        elif error_type == "data_fetch_failed":
             status_code = 500
        elif error_type == "unexpected_error":
             status_code = 500
        # Add more specific mappings if the logic module defines more error types

        print(f"API Error Response: status={status_code}, type={error_type}, msg={message}") # Log errors server-side
        return jsonify({"error": error_type, "message": message}), status_code
    # No error found in the dictionary
    return None


# --- API Endpoints ---

@app.route('/relationships', methods=['GET'])
def get_relationships():
    """API endpoint calling fetch_relative_values."""
    try:
        # Call the imported function directly
        result = fetch_relative_values()
    except sqlite3.Error as e:
         # Catch DB errors that might occur outside the logic function's own try-except
         # (e.g., potentially during initial connection if not caught inside)
         print(f"API layer caught DB error for /relationships: {e}")
         return jsonify({"error": "database_error", "message": f"Database connection or query failed at API level: {e}"}), 500
    except Exception as e:
         # Catch any other unexpected errors during the call
         print(f"API layer caught unexpected error for /relationships: {e}")
         return jsonify({"error": "unexpected_error", "message": f"An unexpected error occurred at API level: {e}"}), 500

    # Check if the logic function returned an error dictionary
    error_response = handle_logic_error(result)
    if error_response:
        return error_response

    # Handle case where DB exists but table is empty (returns empty dict)
    if isinstance(result, dict) and not result:
        return jsonify([]) # Return empty list as per previous design

    # Format the result dictionary {(type_a, type_b): stats} into a JSON list
    # Check if it's the expected dictionary format before processing
    if isinstance(result, dict):
        relationships_list = []
        for (type_a, type_b), stats in result.items():
            relationships_list.append({
                "type_a": type_a,
                "type_b": type_b,
                # Use .get with default for robustness against missing keys in stats
                "average_ratio": round(stats.get('average_ratio', 0), 3),
                "trade_count": stats.get('trade_count', 0)
            })
        return jsonify(relationships_list)
    else:
        # Should not happen if logic function works as documented, but handle defensively
        print(f"Unexpected result type from fetch_relative_values: {type(result)}")
        return jsonify({"error": "internal_server_error", "message": "Received unexpected data format from logic layer."}), 500


@app.route('/hypotrade', methods=['GET'])
def api_hypotrade():
    """API endpoint calling calculate_trade_analysis."""
    # --- Get and Validate Query Parameters ---
    off_t = request.args.get('off_t')
    off_a_str = request.args.get('off_a')
    req_t = request.args.get('req_t')
    req_a_str = request.args.get('req_a')

    missing_params = []
    if not off_t: missing_params.append("off_t")
    if not off_a_str: missing_params.append("off_a")
    if not req_t: missing_params.append("req_t")
    if not req_a_str: missing_params.append("req_a")

    if missing_params:
        return jsonify({"error": "missing_parameters", "message": f"Missing required query parameters: {', '.join(missing_params)}"}), 400

    try:
        # Convert amounts to integers for the logic function
        off_a = int(off_a_str)
        req_a = int(req_a_str)
        # Basic validation as expected by the logic function's docstring
        if off_a <= 0 or req_a <= 0:
             raise ValueError("Amounts must be positive integers.")
    except ValueError as e:
        return jsonify({"error": "invalid_parameter_type", "message": f"Invalid amount provided: {e}. Amounts must be positive integers."}), 400

    # --- Call Logic Function ---
    # No try-except needed here as the provided logic function handles internal errors
    result = hypotrade(off_t, off_a, req_t, req_a)

    # --- Handle Potential Errors Returned by Logic ---
    error_response = handle_logic_error(result)
    if error_response:
        return error_response

    # --- Return Success Response ---
    # The result should be the analysis dictionary directly
    return jsonify(result)


@app.route('/equivalents', methods=['GET'])
def api_oneofthisequals():
    """API endpoint calling calculate_equivalents."""
    # --- Get and Validate Query Parameters ---
    base_type = request.args.get('base_type')
    base_quantity_str = request.args.get('base_quantity')

    missing_params = []
    if not base_type: missing_params.append("base_type")
    if not base_quantity_str: missing_params.append("base_quantity")

    if missing_params:
         return jsonify({"error": "missing_parameters", "message": f"Missing required query parameters: {', '.join(missing_params)}"}), 400

    try:
        # Convert quantity to float for the logic function
        base_quantity = float(base_quantity_str)
         # Basic validation as expected by the logic function's docstring
        if base_quantity <= 0:
             raise ValueError("Base quantity must be positive.")
    except ValueError as e:
        return jsonify({"error": "invalid_parameter_type", "message": f"Invalid base_quantity provided: {e}. Must be a positive number."}), 400

    # --- Call Logic Function ---
    # No try-except needed here as the provided logic function handles internal errors
    result = oneofthisequals(base_type, base_quantity)

    # --- Handle Potential Errors Returned by Logic ---
    error_response = handle_logic_error(result)
    if error_response:
        return error_response

    # --- Return Success Response ---
    # The result should be the equivalents dictionary directly
    return jsonify(result)


# --- Run the App ---
if __name__ == "__main__":
    # Use the imported constant to show the DB path being used by the logic module
    print(f"--- Trade Ratio API ---")
    print(f"Attempting to use database configured as: {RATIO_DATABASE_NAME}")
    print(f"Starting Flask server...")
    # Runs the Flask development server
    # host='0.0.0.0' makes it accessible from other devices on the network
    # debug=True enables auto-reloading on code changes and detailed error pages
    # Important: Set debug=False in a production environment!
    app.run(host='0.0.0.0', port=5001, debug=True)