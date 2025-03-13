FROM python:3.11
LABEL authors="bell77m"

RUN apt-get update
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.compiler.app:app", "--host", "0.0.0.0", "--port", "8000"]
