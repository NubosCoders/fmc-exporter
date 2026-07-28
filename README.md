# fmc-exporter

Small HTTP collector for Cisco Secure Firewall Management Center (FMC) VPN
tunnel status. It exposes data for Zabbix or another HTTP client without
requiring a shared JSON file.

## Quick start

1. Copy `.env.example` to `.env` and set the FMC URL and credentials.
2. Start the exporter:

   ```sh
   docker compose up --build -d
   ```

3. Check the API:

   ```sh
   curl http://localhost:8081/health
   curl http://localhost:8081/tunnels
   ```

The collector stays available while FMC is unreachable. `/health` reports the
collector state, last attempt/success/error timestamps, and FMC connectivity.
`/tunnels` returns the latest successful snapshot and counts `up`, `down`, and
`unknown` states.

## TLS

Certificate verification is enabled by default. For an FMC signed by a private
CA, the exporter first uses the container's system CA store. If the CA is not
installed there, keep the real certificate outside Git and mount it at runtime:

```yaml
services:
  fmc-collector:
    volumes:
      - ./certs/fmc-ca.crt:/certs/fmc-ca.crt:ro
    environment:
      FMC_CA_BUNDLE: /certs/fmc-ca.crt
```

Save this as `compose.override.yaml` and run:

```sh
docker compose -f docker-compose.yaml -f compose.override.yaml up --build -d
```

`FMC_TLS_VERIFY=false` is available only for temporary troubleshooting and
should not be used in production.

Older FMC certificates may contain only a Common Name and no Subject Alternative
Name. The preferred fix is to issue a certificate with a matching SAN. As a
compatibility measure, `FMC_TLS_VERIFY_HOSTNAME=false` disables only hostname
matching; CA chain verification through `FMC_CA_BUNDLE` remains enabled.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `FMC_URL` | `https://fmc.example.local` | FMC base URL |
| `FMC_USER` | required | FMC API username |
| `FMC_PASSWORD` | required | FMC API password |
| `FMC_CA_BUNDLE` | empty | Path to a mounted private CA |
| `FMC_TLS_VERIFY` | `true` | Enable server certificate verification |
| `FMC_TLS_VERIFY_HOSTNAME` | `true` | Verify that certificate SAN matches `FMC_URL` |
| `FMC_TRUST_ENV` | `false` | Use ambient proxy and Requests environment settings |
| `CONNECT_TIMEOUT` | `5` | Connection timeout in seconds |
| `READ_TIMEOUT` | `30` | Response timeout in seconds |
| `UPDATE_INTERVAL` | `60` | Poll interval in seconds |
| `HTTP_PORT` | `8080` | Container HTTP port |
| `EXPORTER_PORT` | `8081` | Published host port |
| `OUTPUT_FILE` | empty | Optional atomic JSON snapshot path |

If `OUTPUT_FILE` is set in Docker, mount its parent directory writable by the
container's unprivileged `exporter` user.

## Development

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The full PostgreSQL and Zabbix demonstration stack is kept separately in
`examples/zabbix-stack.yaml`.
