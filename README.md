# Teledeck

"I know came across this a great photo somwehere... where was it again?"

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
Full install instructions are forthcoming.

Requirements:
- Golang >=1.24
- Python >= 3.9

Instructions:
- Clone the repo.
- Activate Python environment with requirements.txt
- Run `make update` to pull Telegram updates. It will search for a folder called Teledeck.
- `make dev` to run the Go server. The application will open on http://localhost:4000 by default.

Tagging and aesthetic score servers:
- Update Python virtual environment with AI/requirements.txt
- Download eva-2 tagger and aesthetic-shadow aesthetic score to AI/models dir (TODO: use HF cache or automate this?)
- Run python ai/tagger.py to launch the server. Tagging functionality will then be available.


## Example commands
Export channel messages
``` python admin/admin.py --export-channel [name] --export-path export/[name] --message-limit 50 ```
