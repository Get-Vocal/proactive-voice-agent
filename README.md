![logo](assets/logo.webp)

# :robot: Proactive Voice Agent

Demo of Mistral plugged into Retell, see the [demo](https://x.com/eliotthoff/status/1783980026649625032).

## Steps to run locally

1. First install dependencies

```bash
poetry install
```

2. Fill out the API keys in `env.sh`

3. In another bash, use `ngrok` or `cloudflared` to expose the port `8080` to public network.

```bash
make host-url
```

2. Update the host name and export the environment variables.

```
source env.sh
```

4. Start the websocket server

```bash
make app-start
```

The custom LLM URL (to enter in Retell) would look like
`wss://henry-corrected-julia-drive.trycloudflare.com/llm-websocket`
