FROM python

WORKDIR /app

COPY .streamlit ./.streamlit

COPY pages ./pages

COPY setup_nltk.py .
COPY requirements.txt .
COPY utility_functions.py .
RUN pip install -r requirements.txt
COPY logo_one.png . 
RUN python setup_nltk.py
COPY Home.py .


ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]