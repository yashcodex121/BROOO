FROM python:3.10-slim

RUN apt-get update && apt-get install -y 
ffmpeg 
gcc 
git 
python3-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
