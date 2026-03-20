FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# copy requirements FIRST
COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install Node.js 20
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# copy project AFTER node/python is installed
COPY . /app/

# Install node dependencies inside container (root + frontend)
RUN npm install
RUN cd frontend && npm install

EXPOSE 8000 5173

CMD sh -c "cd frontend && npm run dev -- --host & python manage.py runserver 0.0.0.0:8000"
