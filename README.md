# Bitget API Connector

Python connector for Bitget cryptocurrency exchange API.

## Features

- Spot trading
- USDT Perpetual futures
- WebSocket connections
- Rate limiting
- Comprehensive error handling

## Setup

1. Copy `config.example.json` to `config.json`
2. Fill in your API credentials:
   ```json
   {
       "apiKey": "your_api_key_here",
       "secretKey": "your_secret_key_here", 
       "passphrase": "your_passphrase_here"
   }
   ```
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The `config.json` file contains all necessary settings:

- **API Credentials**: apiKey, secretKey, passphrase
- **Endpoints**: baseURL, wsURL, privateWsURL  
- **Trading Settings**: default order types, limits, margin mode
- **Rate Limiting**: requests per second and burst limits

## Security Note

Never commit your real `config.json` with API keys to version control. Always use the `config.example.json` template and fill in your credentials locally.

## Project Structure

- `Spot/` - Spot trading functionality
- `USDT Perp/` - USDT Perpetual futures
- `docs/` - Documentation
- `config.example.json` - Configuration template
- `requirements.txt` - Python dependencies

## Usage

[Add usage examples here]

## License

[Add license information]
