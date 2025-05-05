#SKAPAR EN LISTA UTAV TRADES

trades_file = "/Users/rasmusalpsten/Drive C/Code/Python Projects/Tickettrader"

def text_to_list(file):
    try:
        with open(file, 'r', encoding='utf-8') as file:
            # Read all lines and remove trailing newline characters
            lines = [line.rstrip() for line in file]
        return lines
    except FileNotFoundError:
        print(f"Error: File not found at {file}")
        return []  # Return an empty list, not None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return []  # Return an empty list on other errors as well

if __name__ == "__main__":
    print(text_to_list(trades_file))
    print(len(text_to_list(trades_file)))

