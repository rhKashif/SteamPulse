FROM python

WORKDIR /app

COPY .streamlit ./.streamlit

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app.py .


ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]