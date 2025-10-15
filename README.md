# Teledeck

"I saw the perfect meme for this yesterday... where was it again?"

Teledeck is an AI-powered social media aggregator and image analysis tool designed to put you in control of your digital media library.

## Why Teledeck?

The lines between personal libraries and social media feeds are increasingly blurred. Art is often shared with minimal context, and keeping up with hundreds of accounts relies on opaque "for you" algorithms. Major platforms intentionally obscure their search with opaque algorithms to keep you browsing, while many artists prefer personal channels or gallery sites with limited search capabilities on platforms like Telegram.

Teledeck offers an all-in-one solution to these challenges:

- **AI-Powered Organization**: Utilizes cutting-edge AI models for tagging, rating, and captioning to intelligently annotate your files.
- **Social-Media First**: Source URLs, favorite counts, and other social media metadata stay attached so you never lose track of where something came from.
- **Search without the BS**: Straightforward sorting, filtering, and ranking tools help you find exactly what you are looking for.
- **Unified Media Management**: Aggregates content from various sources into a single, easily navigable library.
- **Responsive Design**: Features a snappy HTMX frontend for smooth performance on both desktop and mobile devices.

Teledeck allows you to organize, search and manage your media on your own terms.



## Installation
Setup Python environment:
```bash
uv venv
uv pip install -r requirements.txt
```


Follow the instructions [here](https://docs.telethon.dev/en/stable/basic/signing-in.html) to set up a Telegram API ID and hash for your account. Add the values to configuration and login:

```bash
cp .env.example .env
cp config.example.yml config.yml
make login
```

```bash
make update-channels
```

```bash
make update
```


Requirements:
- Golang >=1.24
- Python >= 3.9

Instructions:
- Clone the repo.
- Activate Python environment with requirements.txt
- Copy `config/local.example.yaml` to `config/local.yaml` and fill in Telegram/Twitter secrets or point the paths at your media volume (see `config/README.md` for details).
- Run `make update` to pull Telegram updates. It will search for a folder called Teledeck.
- `make dev` to run the Go server. The application will open on http://localhost:4000 by default.

Tagging and aesthetic score servers:
- Update Python virtual environment with AI/requirements.txt
- Download eva-2 tagger and aesthetic-shadow aesthetic score to AI/models dir (TODO: use HF cache or automate this?)
- Run python ai/tagger.py to launch the server. Tagging functionality will then be available.


## Example commands
Export channel messages
``` python admin/admin.py --export-channel [name] --export-path export/[name] --message-limit 50 ```


# Configuration

## Files
- `default.yaml` – checked-in defaults suitable for development.
- `local.yaml` – optional, ignored by git; override secrets and machine-specific paths here.
- `local.example.yaml` – quick template for generating a local override.

## Load order
1. `default.yaml`
2. `local.yaml` (if present)
3. Environment variables (either the new `SECTION__KEY=value` form or the legacy `PORT`, `MEDIA_PATH`, etc.).

Set `TELEDECK_CONFIG_DIR` to point at a custom configuration directory or `TELEDECK_CONFIG_FILE` to use a single YAML file.

## Environment overrides
- Nested keys can be set with double underscores: `export APP__HTTP_PORT=4001`.
- Legacy names like `PORT`, `TAGGER_URL`, and `TELEGRAM_API_ID` are still honoured for compatibility.

All paths in YAML are relative to the repository by default. Use absolute paths in `local.yaml` for deployments.