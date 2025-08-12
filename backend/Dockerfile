FROM python:3.11-slim
WORKDIR /app

# upgrade pip & wheel
RUN python -m pip install --no-cache-dir --upgrade pip wheel && \
    pip --version

# install project deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy code & default command
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
