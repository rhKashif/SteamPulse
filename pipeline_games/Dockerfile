FROM python

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY pipeline.sh .

COPY extract_games.py .
COPY transform_games.py .
COPY load_games.py .

CMD bash pipeline.sh