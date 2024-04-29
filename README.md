# Proactive Voice Agent

Demo of Mistral plugged into Retell.

## Steps to run locally

1. First install dependencies

```bash
poetry install
```

2. Fill out the API keys in `.env`

3. In another bash, use `ngrok` or `cloudflared` to expose the port `8080` to public network.

```bash
make host-url
```

4. Start the websocket server

```bash
make app-start
```

The custom LLM URL (to enter in Retell) would look like
`wss://henry-corrected-julia-drive.trycloudflare.com/llm-websocket`
