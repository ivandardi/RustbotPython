# RustbotPython

## How to run

Create a `.env` file like so:

```bash
DISCORD_TOKEN=<token here>
```

Then run the following commands:

```bash
 docker build -t rustbotpy -f Containerfile .
 docker run --rm --name rustbotpy --env-file .env rustbotpy
```
