#LÄS IN OCH FÖRSTÅ TRADES

from google import genai
from tradestorer import *
from listgenerator import *
from ratelimiter import * 
from apikey import * 

client = genai.Client(api_key = geminikey) 

trades_file = "/Users/rasmusalpsten/Drive C/Code/Python Projects/Tickettrader"

rate_limiter = RateLimiter(max_calls=13, time_window=60)

def analyze_ticket_exchange(text):
    rate_limiter.check()
    prompt = f"""
    Analyze the following text, which is a request to exchange tickets:
    "{text}"

    Identify the quantity of tickets being offered and the type of ticket,
    and the quantity of tickets being requested and the type of ticket.

    Return the quantity and type of the offered ticket, and the quantity and type of the requested ticket.
    If several ticket types are requested, select only ONE of them.

    Interpret "Yran" as "MÖ", "Skvalborg" and/or "Sydskånska" as "SSK", "ÖGS" as "ÖG", "Kvalborg" as "VG/H", "1 maj" as "GBG", "Lunds" as "NSA" and "Sunwing" as "HK". 
    These are not exact and may appear in variants. "1 maj" may be written as "första maj", and "NSA" as "Näst siste april" for example. 

    Tickets can only be ONE out of 8 different types.
    These are: GBG, MÖ, NSA, SSK, VG/H, T-Bar, ÖG, HK.

    For example:
    Text: "Har två NSA på Lunds som jag gärna byter till två siste april på ÖG!!"
    Offered:
    Quantity: 2
    Ticket Type: NSA
    Requested:
    Quantity: 2
    Ticket Type: ÖG

    Text: "Har en yran, byter mot en Sunwing"
    Offered:
    Quantity: 1
    Ticket Type: MÖ
    Requested:
    Quantity: 1
    Ticket Type: HK

    Text: "Har en yran som jag gärna byter mot kvalborg på vg/hallands"
    Offered:
    Quantity: 1
    Ticket Type: MÖ
    Requested:
    Quantity: 1
    Ticket Type: VG/H

    Text: "Byter tre skvalborg mot sunwing"
    Offered:
    Quantity: 3
    Ticket Type: SSK
    Requested:
    Quantity: 1
    Ticket Type: HK

    Text: "Hejhopp Byter en 1 maj mot en NSA"
    Offered:
    Quantity: 1
    Ticket Type: GBG
    Requested:
    Quantity: 1
    Ticket Type: NSA

    Text: "Har 2 skvalborg som ja gärna byter mot 2 tbar siste april!!!"
    Offered:
    Quantity: 2
    Ticket Type: SSK
    Requested:
    Quantity: 2
    Ticket Type: T-bar

    Always answer using this exact structure, and always use the short version of the ticket type, for example "GBG" and "SSK."
    """

    try:
        response = client.models.generate_content(
            model = 'gemini-2.0-flash', 
            contents = [prompt]
            )
        # print(response.text) # Debugging
        lines = response.text.split('\n')
        offered_quantity = 0
        offered_ticket_type = ""
        requested_quantity = 0
        requested_ticket_type = ""

        for index, line in enumerate(lines): #Searching for the quantity
            if "Offered:" in line:
                continue
            if "Requested:" in line:
                continue
            if "Quantity:" in line:
                try:
                    quantity_value = line.split(":")[1].strip()
                    if "Offered" in lines[index - 1]: # check the line before if its offered or requested
                         offered_quantity = int(quantity_value) 
                    else:
                         requested_quantity = int(quantity_value)
                except ValueError:
                    pass  # Handle cases where the quantity is not a valid integer
            elif "Ticket Type:" in line:
                ticket_type_value = line.split(":")[1].strip()
                if "Offered" in lines[lines.index(line)-2]: # check 2 lines before if its offered or requested
                    offered_ticket_type = ticket_type_value
                else:
                    requested_ticket_type = ticket_type_value

        return offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type
    except Exception as e:
        print(f"Error analyzing text: {e}")
        pass

def feeder(trade_offer_list):
    for trades in trade_offer_list:
        offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type = analyze_ticket_exchange(trades)
        if offered_quantity is not None: # Only add to the database if analysis was successful
            add_trade_entry(offered_quantity, offered_ticket_type, requested_quantity, requested_ticket_type)
            print(f"Text: \"{trades}\"")
            print(f"Offered Quantity: {offered_quantity}, Ticket Type: {offered_ticket_type}")
            print(f"Requested Quantity: {requested_quantity}, Ticket Type: {requested_ticket_type}")
            print('\n')
        else:
            print(f"Failed to analyze text: \"{trades}\"")
            print('\n')

if __name__ == "__main__": #just makes the code only run when ran in the project, not imported as a module
#     test_texts = [
# "Byter två NSA mot två biljetter till ÖGs",
# "Hejj!! Byter gärna en skvalborg (ssk) mot en yran",
# "Hallojs! Byter gärna min 1a maj mot yran",
# "Byter tre kvalborg mot tre sunwing!"
#     ]
    feeder(text_to_list(trades_file))
    viewdb()