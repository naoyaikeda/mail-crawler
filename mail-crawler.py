import json
import os
from argparse import ArgumentParser
import imaplib
from dotenv import load_dotenv
import gauth
import exauth
import locale
import datetime

imaplib._MAXLINE = 10000000   # Increase the maximum line length for IMAP responses

def add_account():
    config_path = "accounts.json"
    account_info = {}

    account_info['auth_type'] = 'IMAP'
    account_info['email'] = input("Enter email address: ")
    account_info['username'] = input("Enter username: ")
    account_info['password'] = input("Enter password: ")
    account_info['imap_server'] = input("Enter IMAP server: ")
    account_info['imap_port'] = input("Enter IMAP port: ")

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                accounts = []
    else:
        accounts = []

    accounts.append(account_info)

    with open(config_path, 'w') as f:
        json.dump(accounts, f, indent=4)

    print("Account added successfully.")

def add_account_exchange():
    exchange_auth = exauth.ExchangeAuth()

    config_path = "accounts.json"
    account_info = {}

    account_info['auth_type'] = 'EXCHANGE_OAUTH2'
    account_info['email'] = input("Enter email address: ")
    account_info['username'] = account_info['email']
    account_info['imap_server'] = "outlook.office365.com"
    account_info['imap_port'] = 993

    auth_url = exchange_auth.get_auth_url()
    print("Please go to the following URL to authorize the application:")
    print(auth_url)
    auth_url = input("Enter the authorization url: ")

    auth_code = exchange_auth.extract_auth_code(auth_url)

    access_token_response = exchange_auth.get_access_token(auth_code)
    account_info['password'] = access_token_response['access_token']
    account_info['refresh_token'] = access_token_response.get('refresh_token', '')

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                accounts = []
    else:
        accounts = []

    accounts.append(account_info)

    with open(config_path, 'w') as f:
        json.dump(accounts, f, indent=4)

    print("Account added successfully.")

def add_account_gmail():
    google_auth = gauth.GoogleAuth()

    config_path = "accounts.json"
    account_info = {}

    account_info['auth_type'] = 'GMAIL_OAUTH2'
    account_info['email'] = input("Enter email address: ")
    account_info['username'] = account_info['email']
    account_info['imap_server'] = "imap.gmail.com"
    account_info['imap_port'] = 993

    google_auth = gauth.GoogleAuth()
    scope = "https://mail.google.com/"
    auth_url = google_auth.get_auth_url(scope)
    print("Please go to the following URL to authorize the application:")
    print(auth_url)
    auth_code = input("Enter the authorization code: ")

    access_token_response = google_auth.get_access_token(auth_code)
    account_info['password'] = access_token_response['access_token']
    account_info['refresh_token'] = access_token_response.get('refresh_token', '')

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                accounts = []
    else:
        accounts = []

    accounts.append(account_info)

    with open(config_path, 'w') as f:
        json.dump(accounts, f, indent=4)

    print("Account added successfully.")


def clear_accounts():
    config_path = "accounts.json"
    if os.path.exists(config_path):
        os.remove(config_path)
        print("All account configurations have been cleared.")
    else:
        print("No account configurations found to clear.")

def list_accounts():
    config_path = "accounts.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                accounts = []
            for idx, account in enumerate(accounts, start=1):
                print(f"Account {idx}:")
                print(f"  Auth Type: {account['auth_type']}")
                print(f"  Email: {account['email']}")
                print(f"  User name: {account['username']}")
                print(f"  IMAP Server: {account['imap_server']}")
                print(f"  IMAP Port: {account['imap_port']}")
                print()
    else:
        print("No account configurations found.")

def crawler_accounts(args):
    accounts = []
    config_path = "accounts.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                print("No valid account configurations found.")
                return
    else:
        print("No account configurations found.")
        return
    
    scaning_addresses_path = "scan_addresses.txt"
    scan_addresses = set()
    if os.path.exists(scaning_addresses_path):
        with open(scaning_addresses_path, 'r') as f:
            for line in f:
                address = line.strip()
                if address:
                    scan_addresses.add(address)
    
    for account in accounts:
        try:
            if account['auth_type'] == 'GMAIL_OAUTH2':
                def attempt_login(token):
                    access_token = token
                    auth_string = f"user={account['username']}\1auth=Bearer {access_token}\1\1"
                    mail = imaplib.IMAP4_SSL(account['imap_server'], int(account['imap_port']))
                    mail.authenticate('XOAUTH2', lambda x: auth_string)
                    return mail

                try:
                    mail = attempt_login(account['password'])
                except imaplib.IMAP4.error:
                    google_auth = gauth.GoogleAuth()
                    refresh_response = google_auth.refresh_access_token(account['refresh_token'])
                    new_access_token = refresh_response['access_token']
                    account['password'] = new_access_token
                    with open(config_path, 'r') as f:
                        all_accounts = json.load(f)
                    for acc in all_accounts:
                        if acc['email'] == account['email']:
                            acc['password'] = new_access_token
                    with open(config_path, 'w') as f:
                        json.dump(all_accounts, f, indent=4)
                    mail = attempt_login(new_access_token)

            elif account['auth_type'] == 'EXCHANGE_OAUTH2':
                # Exchange Online (Outlook.office365.com) も XOAUTH2 を使用
                access_token = account['password']
                # XOAUTH2 認証文字列は Gmail と同じ形式
                auth_string = f"user={account['username']}\1auth=Bearer {access_token}\1\1"
                mail = imaplib.IMAP4_SSL(account['imap_server'], int(account['imap_port']))
                mail.authenticate('XOAUTH2', lambda x: auth_string)
            elif account['auth_type'] == 'IMAP':
                mail = imaplib.IMAP4_SSL(account['imap_server'], int(account['imap_port']))
                mail.login(account['username'], account['password'])

            mail.select("inbox")
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()
            print(f"Account: {account['email']} - Total Emails: {len(email_ids)}")

            today = datetime.date.today()
            start_date = today - datetime.timedelta(days=args.scan_delta_days)
            start_date_str = start_date.strftime("%d-%b-%Y")

            for address in scan_addresses:
                status, msg_ids = mail.search(None, f'(FROM "{address}" SINCE {start_date_str})')
                msg_id_list = msg_ids[0].split()
                mails = len(msg_id_list)
                if mails > 0:
                    print(f"  From: {address} - Emails Found Since {start_date_str}: {mails}")

            mail.logout()
        except Exception as e:
            print(f"Failed to crawl account {account['email']}: {e}")

def execute_command(args, command):
    if command == "clear":
        clear_accounts()
    elif command == "add":
        add_account()
    elif command == "add_gmail":
        add_account_gmail()
    elif command == "add_exchange":
        add_account_exchange()
    elif command == "list":
        list_accounts()
    elif command == "crawl":
        crawler_accounts(args)

def initialize_locale():
    try:
        locale.setlocale(locale.LC_ALL, 'C')
    except locale.Error as e:
        print(f"Warning: Unable to set locale: {e}")

def main():
    initialize_locale()

    load_dotenv()
    gmail_client_id = os.getenv("GMAIL_CLIENT_ID")
    gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET")

    parser = ArgumentParser(description="Mail Crawler Configuration Loader")
    parser.add_argument("command", choices=["clear", "add", "add_gmail", "add_exchange", "list", "crawl"], help="Command to execute")
    parser.add_argument("--scan-delta-days", type=int, default=2, help="Number of days to look back for scanning emails")

    args = parser.parse_args()
    execute_command(args, args.command)

if __name__ == "__main__":
    main()
