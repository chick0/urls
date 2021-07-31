# URLs

Simple URL Shorter

## How to run
1. Install requirements
   ```bash
   pip install -r requirements.txt
   ```

2. Set Database connection URL
   ```bash
   export urls_sql='mysql://<id>:<password>@<host>:<port>/<db name>'
   ```

3. do database migration
   ```bash
   flask db upgrade
   ```

4. Launch Server
   ```bash
   uvicorn --port 8000 --loop uvloop --interface wsgi --factory app:create_app
   ```

## Setting Superuser

1. Run `config.py` to create config file.

2. Edit `superuser.ini` to log in to the superuser dashboard.
