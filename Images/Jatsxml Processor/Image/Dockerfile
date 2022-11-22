FROM python:3.11.0-slim-bullseye

RUN apt-get update -y
RUN apt-get install -y wget
RUN apt-get install -y curl
run apt-get install -y build-essential
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN chmod +x mariadb_repo_setup
RUN ./mariadb_repo_setup \
   --mariadb-server-version="mariadb-10.9.4"

RUN apt-get install -y libmariadb3 libmariadb-dev

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/app.py .

CMD ["python","-u","./app.py"]