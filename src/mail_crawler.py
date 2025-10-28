import email
from email.header import decode_header, make_header
import json
import os
from argparse import ArgumentParser
import imaplib
from dotenv import load_dotenv
import auth.gauth as gauth
import auth.exauth as exauth
import locale
from config.config import get_config_dir
import datetime
import rich
import rich.console
import rich.markdown

console = rich.console.Console()
imaplib._MAXLINE = 10000000   # Increase the maximum line length for IMAP responses

def decode_subject(subject_raw: str) -> str:
    """MIMEエンコードされた件名をデコードし、プレーンな文字列として返す"""
    if not subject_raw:
        return "(No Subject)"
    # decode_header でタプル (バイト文字列, 文字コード) のリストを取得
    # make_header でこれを結合し、最終的な文字列に変換
    return str(make_header(decode_header(subject_raw)))

def add_account():
    config_path = get_config_dir() / "accounts.json"
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

    config_path = get_config_dir() / "accounts.json"
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

    config_path = get_config_dir() / "accounts.json"
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
    config_path = get_config_dir() / "accounts.json"
    if os.path.exists(config_path):
        os.remove(config_path)
        print("All account configurations have been cleared.")
    else:
        print("No account configurations found to clear.")

def list_accounts():
    config_path = get_config_dir() / "accounts.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                accounts = []
            for idx, account in enumerate(accounts, start=1):
                console.print(f"Account {idx}:")
                console.print(f"  Auth Type: {account['auth_type']}")
                console.print(f"  Email: {account['email']}")
                console.print(f"  User name: {account['username']}")
                console.print(f"  IMAP Server: {account['imap_server']}")
                console.print(f"  IMAP Port: {account['imap_port']}")
                console.print()
    else:
        console.print("No account configurations found.")

def crawl_gmail_account(account, accounts, config_path):
    google_auth = gauth.GoogleAuth()

    def attempt_login(token):
        access_token = token
        auth_string = f"user={account['username']}\1auth=Bearer {access_token}\1\1"
        mail = imaplib.IMAP4_SSL(account['imap_server'], int(account['imap_port']))
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        return mail

    try:
        mail = attempt_login(account['password'])
    except imaplib.IMAP4.error as first_error:
        refresh_token = account.get('refresh_token')

        if 'AUTHENTICATIONFAILED' in str(first_error) and refresh_token:
            console.print(f"[{account['email']}] Token expired. Attempting refresh...")

            refresh_response = google_auth.refresh_access_token(refresh_token)
            new_access_token = refresh_response['access_token']

            account['password'] = new_access_token
            if 'refresh_token' in refresh_response:
                account['refresh_token'] = refresh_response['refresh_token']

            mail = attempt_login(new_access_token)
            console.print(f"[{account['email']}] Token refreshed and login successful.")

            with open(config_path, 'w') as f:
                json.dump(accounts, f, indent=4)
        else:
            raise first_error
    return mail

def crawl_exchange_account(account, accounts, config_path):
    exchange_auth = exauth.ExchangeAuth()

    def attempt_login_exchange(token):
        access_token = token
        auth_string = f"user={account['username']}\1auth=Bearer {access_token}\1\1"
        mail = imaplib.IMAP4_SSL(account['imap_server'], int(account['imap_port']))
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        return mail

    try:
        mail = attempt_login_exchange(account['password'])
    except imaplib.IMAP4.error as first_error:
        refresh_token = account.get('refresh_token')

        if 'AUTHENTICATE failed.' in str(first_error) and refresh_token:
            console.print(f"[{account['email']}] Exchange Token expired. Attempting refresh...")

            refresh_response = exchange_auth.refresh_access_token(refresh_token)
            new_access_token = refresh_response['access_token']

            account['password'] = new_access_token
            if 'refresh_token' in refresh_response:
                account['refresh_token'] = refresh_response['refresh_token']

            mail = attempt_login_exchange(new_access_token)
            console.print(f"[{account['email']}] Exchange Token refreshed and login successful.")

            with open(config_path, 'w') as f:
                json.dump(accounts, f, indent=4)
        else:
            raise first_error
    return mail

def crawler_accounts(args):
    accounts = []
    config_path = get_config_dir() / "accounts.json"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            try:
                accounts = json.load(f)
            except json.JSONDecodeError:
                console.print("No valid account configurations found.")
                return
    else:
        console.print("No account configurations found.")
        return
    
    scan_addresses = read_scan_addresses()
    

    for account in accounts:
        try:
            if account['auth_type'] == 'GMAIL_OAUTH2':
                mail = crawl_gmail_account(account, accounts, config_path)
            elif account['auth_type'] == 'EXCHANGE_OAUTH2':
                mail = crawl_exchange_account(account, accounts, config_path)
            elif account['auth_type'] == 'IMAP':
                mail = imap_open(account)
            else:
                console.print(f"Unsupported auth type for account {account['email']}")
                continue

            mail.select("inbox")
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()
            console.print(f"Account: {account['email']} - Total Emails: {len(email_ids)}")

            today = datetime.date.today()
            start_date = today - datetime.timedelta(days=args.scan_delta_days)
            start_date_str = start_date.strftime("%d-%b-%Y")

            for address in scan_addresses:
                status, msg_ids = mail.search(None, f'(FROM "{address}" SINCE {start_date_str})')
                msg_id_list = msg_ids[0].split()
                mails = len(msg_id_list)
                if mails > 0:
                    for msg_id in msg_id_list:
                        status, msg_data = mail.fetch(msg_id, '(RFC822)')
                        msg = email.message_from_bytes(msg_data[0][1])
                        subject = decode_subject(msg['subject'])
                        console.print(f"    Email ID: {msg_id.decode()} - Subject: {subject}")

                    console.print(f"  From: {address} - Emails Found Since {start_date_str}: {mails}")

            mail.logout()
        except Exception as e:
            console.print(f"Failed to crawl account {account['email']}: {e}")

def read_scan_addresses():
    scaning_addresses_path = get_config_dir() / "scan_addresses.txt"
    scan_addresses = set()
    if os.path.exists(scaning_addresses_path):
        with open(scaning_addresses_path, 'r') as f:
            for line in f:
                address = line.strip()
                if address:
                    scan_addresses.add(address)
    return scan_addresses

def imap_open(account):
    mail = imaplib.IMAP4_SSL(account['imap_server'], int(account['imap_port']))
    mail.login(account['username'], account['password'])
    return mail

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

    load_dotenv(dotenv_path=get_config_dir() / ".env")
    gmail_client_id = os.getenv("GMAIL_CLIENT_ID")
    gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET")

    parser = ArgumentParser(description="Mail Crawler Configuration Loader")
    parser.add_argument("command", choices=["clear", "add", "add_gmail", "add_exchange", "list", "crawl"], help="Command to execute")
    parser.add_argument("--scan-delta-days", type=int, default=2, help="Number of days to look back for scanning emails")

    args = parser.parse_args()
    execute_command(args, args.command)

if __name__ == "__main__":
    main()
