FROM python

WORKDIR /app

COPY .streamlit ./.streamlit

COPY pages ./pages

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY Home.py .


ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]