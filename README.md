# ChatGPT Auto Bot - Registration & Payment

Automated bot for ChatGPT account registration and workspace subscription payment.

## Features

- ✅ Automatic ChatGPT account registration
- ✅ Temporary email integration (TempMail API)
- ✅ OTP verification
- ✅ Workspace subscription payment via Stripe
- ✅ Auto card generation from BIN
- ✅ Korean identity generation (API + fallback)
- ✅ BIN storage for reuse
- ✅ Batch registration support
- ✅ Cloudflare bypass with curl_cffi
- ✅ Telegram Bot integration for remote control
- ✅ Supabase database integration for data storage

## Installation

1. Install Python 3.12+

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from example:
```bash
cp .env.example .env
```

4. Edit `.env` with your configuration:
```env
# TempMail API (get from https://tempmail.lol)
TEMPMAIL_API_KEY=your_api_key_here

# ChatGPT default password
CHATGPT_PASSWORD=YourSecurePassword123!

# Supabase Database
DATABASE_URL=postgresql://user:password@host:port/database

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_IDS=your_chat_id
```

5. Setup Supabase database:
   - Go to your Supabase project → SQL Editor
   - Copy and paste content from `database_setup.sql`
   - Click "Run" to create all tables and insert 100 Korean addresses
   - Verify: Check Tables section to see all 6 tables created

## Usage

### Telegram Bot Mode (Recommended)

Run the Telegram bot:
```bash
python bot_main.py
```

Features:
- Remote control via Telegram
- Register accounts
- Manage proxies and BINs
- Upgrade accounts to Plus/Team
- View logs and statistics

### CLI Mode

Run the CLI:
```bash
python main.py
```

### Options

1. **Register single account** - Register one ChatGPT account
2. **Register multiple accounts** - Batch register multiple accounts
3. **Register + Subscribe to workspace** - Register and immediately subscribe
4. **Subscribe existing account to workspace** - Add workspace subscription to existing account
5. **Exit**

## Project Structure

```
chatgpt-auto-bot/
├── main.py                    # CLI entry point
├── bot_main.py                # Telegram bot entry point
├── src/
│   ├── register/              # Registration module
│   │   ├── email_service.py   # TempMail API
│   │   ├── chatgpt_api.py     # ChatGPT Auth API
│   │   └── register_bot.py    # Registration orchestrator
│   ├── payment/               # Payment module
│   │   ├── payment_api.py     # ChatGPT Payment API
│   │   ├── stripe_api.py      # Stripe Payment API
│   │   ├── stripe_converter.py # Link converter
│   │   └── payment_bot.py     # Payment orchestrator
│   ├── telegram/              # Telegram bot module
│   │   ├── bot.py             # Bot main
│   │   ├── handlers.py        # Command handlers
│   │   ├── keyboards.py       # Inline keyboards
│   │   └── messages.py        # Message templates
│   ├── database/              # Database module
│   │   ├── connection.py      # Database connection
│   │   ├── models.py          # SQLAlchemy models
│   │   └── repository.py      # CRUD operations
│   └── utils/
│       ├── http_client.py     # HTTP client with Cloudflare bypass
│       ├── logger.py          # Logging
│       ├── config.py          # Configuration
│       ├── token_helper.py    # Token management
│       ├── card_generator.py  # Card generation from BIN
│       └── korean_identity.py # Korean identity generator
├── config/
│   └── settings.yaml          # Settings
├── logs/                      # Log files
├── accounts.json              # Registered accounts (fallback)
├── database_setup.sql         # Database setup script (run in Supabase)
├── .env                       # Environment variables
└── requirements.txt           # Dependencies
```

## Registration Flow

1. **Visit Homepage** - Initialize session
2. **Get CSRF Token** - Fetch CSRF token
3. **Signin Redirect** - Get authentication URL
4. **Follow Auth Redirect** - Follow redirect to auth.openai.com
5. **Register Account** - Create account with email/password
6. **Send OTP** - Request OTP code
7. **Validate OTP** - Verify OTP from email
8. **Create Profile** - Set name and birthdate

## Payment Flow

1. **Get Countries** - Fetch available countries
2. **Input BIN** - User provides card BIN (saved to `card_bin.txt` for reuse)
3. **Generate Card** - Auto-generate card number with valid Luhn checksum
4. **Generate Korean Identity** - Fetch from randomuser.me API or generate randomly
5. **Create Checkout Session** - Create ChatGPT checkout session
6. **Convert to Stripe URL** - Convert session ID to Stripe payment URL
7. **Create Payment Method** - Create Stripe payment method with generated card
8. **Confirm Payment** - Confirm payment (may require captcha)

## Card Generation

The bot automatically generates valid card details from your BIN:

1. **First time**: Enter your card BIN (first 6-8 digits)
2. **BIN is saved** to `card_bin.txt` for future use
3. **Next time**: Bot asks if you want to reuse saved BIN
4. **Auto-generates**:
   - Full 16-digit card number with valid Luhn checksum
   - Random expiry date (2026-2030)
   - Random CVV (3 digits)

## Korean Identity

The bot automatically generates Korean billing information:

1. **Try API first**: Fetch from randomuser.me API (Korean nationality)
2. **Fallback**: Generate random Korean name if API fails
3. **Includes**:
   - Korean name (romanized)
   - Email address
   - Phone number (Korean format)

## Important Notes

### Card BIN

- First time: Enter your card BIN (6-8 digits)
- BIN is saved to `card_bin.txt` for reuse
- Next time: Bot will ask if you want to use saved BIN
- Card numbers are generated with valid Luhn checksum

### Korean Identity

- Bot tries to fetch real Korean identity from randomuser.me API
- If API fails, generates random Korean name
- All names are romanized for international use

### Captcha Handling

The bot may encounter hCaptcha during payment:
- **Passive Captcha**: Automatically handled with `passive_captcha_token`
- **Challenge Captcha**: Requires manual intervention (select images)

If captcha is required, the bot will provide the Stripe URL for manual completion.

### Access Token

Access token is automatically fetched from session cookies after registration.

### Cloudflare Bypass

Uses `curl_cffi` with `impersonate="chrome120"` to bypass Cloudflare protection.

## Configuration

Edit `config/settings.yaml` to customize:

```yaml
chatgpt:
  base_url: "https://chatgpt.com"
  auth_base_url: "https://auth.openai.com"
  timeout: 30

tempmail:
  base_url: "https://tempmail.lol"
  timeout: 30

registration:
  first_names: [...]
  last_names: [...]
  birth_year_min: 1985
  birth_year_max: 2000
```

## Troubleshooting

### Registration Issues

- **403 Cloudflare Error**: Make sure `curl_cffi` is installed correctly
- **Cookie Conflict**: Bot handles cookies manually to avoid conflicts
- **OTP Not Received**: Check TempMail API key and email service

### Payment Issues

- **No Access Token**: Make sure registration completed successfully
- **Captcha Required**: Complete captcha manually using provided Stripe URL
- **Payment Failed**: Check card details and billing information

## Telegram Bot

The bot includes a Telegram interface for remote control.

### Quick Setup
1. Create bot with @BotFather on Telegram
2. Get your Chat ID from @userinfobot
3. Add to `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_ADMIN_IDS=your_chat_id
   ```
4. Run: `python bot_main.py`
5. Send `/start` to your bot

### Commands
- `/start` - Start bot and show menu
- `/register` - Register new ChatGPT accounts
- `/accounts` - View account list
- `/upgrade` - Upgrade account to Plus/Team
- `/status` - Check system status
- `/config` - View configuration

## Supabase Database

The bot uses Supabase PostgreSQL for data storage.

### Quick Setup
1. Create Supabase project at https://supabase.com
2. Go to SQL Editor
3. Copy and paste `database_setup.sql` content
4. Click "Run" to create all tables
5. Add DATABASE_URL to `.env`:
   ```env
   DATABASE_URL=postgresql://user:pass@host:port/database
   ```

### Tables Created
- `accounts` - ChatGPT accounts with cookies
- `payments` - Payment transaction history
- `card_bins` - Card BINs with success/fail stats
- `proxies` - Proxy management with performance tracking
- `korean_addresses` - 100 Korean addresses for billing
- `logs` - Application logs

### Features
- Track BIN and proxy success rates
- Smart proxy selection by country
- Payment history tracking
- Automatic log cleanup (30 days)

## Dependencies

- `curl_cffi==0.7.3` - Cloudflare bypass
- `httpx` - HTTP client
- `pydantic` - Data validation
- `loguru` - Logging
- `pyyaml` - YAML configuration
- `python-dotenv` - Environment variables
- `python-telegram-bot==21.0` - Telegram bot (optional)
- `psycopg2-binary` - PostgreSQL adapter (optional)
- `sqlalchemy` - ORM for database (optional)

## License

MIT License

## Disclaimer

This bot is for educational purposes only. Use responsibly and comply with ChatGPT's Terms of Service.
