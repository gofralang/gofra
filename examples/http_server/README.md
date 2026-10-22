# HTTP server example

Opens an HTTP server on `127.0.0.1:8080` and responds with a simple HTML page.

## Run

```bash
poetry run python -m gofra run examples/http_server/main.gof
```

## Check

```bash
curl -i http://127.0.0.1:8080/
```

Expected response:

```
HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<h1>Hello from Gofra HTTP server!</h1><i>Built with Gofra and native HTTP library</i>
```
