# UBS to YNAB Web App

This subfolder contains a small Flask web application with its own converter module for the shared CSV-to-YNAB business logic.

## Run locally

From the repository root:

```bash
uv run --project webapp flask --app webapp/app run --debug
```

Then open the local address shown in the terminal, upload one or more CSV files, and download the converted YNAB file or ZIP archive.

## Run with Docker

Build the image from the repository root:

```bash
docker build -t ubs-to-ynab-web ./webapp
```

Run the container:

```bash
docker run --rm -p 8000:8000 ubs-to-ynab-web
```

Then open `http://localhost:8000`.

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

Then open `http://localhost:8000`.

Stop it with:

```bash
docker compose down
```

This compose file also includes Traefik labels and expects an external Docker network named `frontend` by default. You can override the hostname, network, and cert resolver with environment variables such as `TRAEFIK_HOST`, `TRAEFIK_NETWORK`, and `TRAEFIK_CERTRESOLVER`.

## Move to another machine

The easiest option is to copy the project folder and build it there:

```bash
docker compose up --build
```

If you want to transfer a prebuilt image instead of the source code:

```bash
docker image save ubs-to-ynab-web -o ubs-to-ynab-web.tar
```

Copy `ubs-to-ynab-web.tar` to the other machine, then load it there:

```bash
docker image load -i ubs-to-ynab-web.tar
docker run --rm -p 8000:8000 ubs-to-ynab-web
```

## Notes

- One uploaded file returns one `.csv` download.
- Multiple uploaded files return a `.zip` containing each converted YNAB CSV.
- If one or more files fail during a multi-file upload, the ZIP also includes a `conversion_report.txt` file with the failures.
- The Docker image runs behind `gunicorn` for production use.
