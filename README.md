# mail-crawler

`mail-crawler` is a tool for crawling and checking email accounts.

## Features

- Supports IMAP, Gmail (OAuth2), and Exchange (OAuth2) accounts.
- Add and manage multiple email accounts.
- Crawl emails from specific senders within a given time frame.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/mail-crawler.git
    cd mail-crawler
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Setup

1.  **Create a `.env` file in the configuration directory (`~/.mail-crawler`).**
    ```bash
    touch ~/.mail-crawler/.env
    ```
2.  **Add the following environment variables to the `.env` file:**
    -   For Gmail, you will need to create a project in the Google Cloud Platform Console and get OAuth 2.0 Client credentials.
        -   `GMAIL_CLIENT_ID`
        -   `GMAIL_CLIENT_SECRET`
    -   For Exchange, you will need to register an application in the Azure portal and get an application (client) ID and a client secret.
        -   `EXCHANGE_CLIENT_ID`
        -   `EXCHANGE_CLIENT_SECRET`

3.  **Create a `scan_addresses.txt` file in the configuration directory (`~/.mail-crawler`).**
    ```bash
    touch ~/.mail-crawler/scan_addresses.txt
    ```
    Add the email addresses you want to scan for, one per line.

## Usage

### Add an Account

-   **IMAP:**
    ```bash
    python mail-crawler.py add
    ```
-   **Gmail (OAuth2):**
    ```bash
    python mail-crawler.py add_gmail
    ```
-   **Exchange (OAuth2):**
    ```bash
    python mail-crawler.py add_exchange
    ```

### List Accounts

```bash
python mail-crawler.py list
```

### Clear All Accounts

```bash
python mail-crawler.py clear
```

### Crawl Accounts

```bash
python mail-crawler.py crawl --scan-delta-days 7
```
This will crawl all configured accounts and look for emails from the addresses in `scan_addresses.txt` from the last 7 days.
