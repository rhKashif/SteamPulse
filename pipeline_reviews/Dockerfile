FROM python

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY nltk_download.py .
RUN python nltk_download.py

COPY extract.py .
COPY transform.py .
COPY sentiment.py .
COPY load.py .
COPY pipeline.py .

CMD ["python", "pipeline.py"]