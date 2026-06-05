import json
import os
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
import re 
def setup():
    print("\n*********************** RENT FINDER SETUP ***********************\n")
    while True:
        keyword = input('Enter a keyword to look for in (description, address) : ')
        if not len(keyword) > 3:
            print('Invalid keyword, must be at lest 3 characters')
            continue

        confirm = input(f"Look for keyword '{keyword}' (y or n) : ")
        if confirm.lower() == 'y' or confirm.lower() == 'yes':
            keyword = keyword.strip().lower()
            break

        continue


    while True:
        max_price = input('\nEnter a maximum price (e.g. 950) : ')
        try:
            max_price = int(max_price)
            confirm = input(f"Confirm max_price of {max_price} (y or n) : ")
            if confirm.lower() == 'y' or confirm.lower() == 'yes':
                break
            continue
         
        except Exception:
            print('Invalid price , please provide a valid number')

    while True:    

        postal_code = input('\nEnter a specific postal code or press ENTER to ignore : ')
        confirm = input(f"Confirm postal code '{postal_code}' (y or n) : ")
        if confirm.lower() == 'y' or confirm.lower() == 'yes':
            postal_code = re.sub('\s+', '', postal_code.lower())
            break
        continue

    p_alt = postal_code[0:(len(postal_code) // 2)] + " " + postal_code[(len(postal_code) // 2):]
    print(p_alt)

    with open(CONFIG_PATH, 'w') as f:
        f.write(json.dumps({'keyword': keyword, 'max_price': max_price, 
                            'postal_code': postal_code , 'p_alt':p_alt}))
        
        print('Configuration saved in config.json')

setup()