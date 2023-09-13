from os import environ
from dotenv import load_dotenv
import streamlit as st
from re import fullmatch
from psycopg2 import connect, Error
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


def get_db_connection(config) -> connection:
    """Connect to the database with game data"""
    try:
        return connect(
            user=config['DATABASE_USERNAME'],
            password=config['DATABASE_PASSWORD'],
            host=config['DATABASE_ENDPOINT'],
            port=config['DATABASE_PORT'],
            database=config['DATABASE_NAME'],
            cursor_factory=RealDictCursor)
    except (Error, ValueError) as err:
        return f"Error connecting to database. {err}"


def add_email_to_database(conn: connection, email: str) -> None:
    """Add email to database"""
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO user_email(email) VALUES (%s)
                ON CONFLICT (email) DO NOTHING;""",
                    [email])
        conn.commit()
        cur.close()


def get_subscription_count(conn: connection) -> None:
    pass


def main():
    """Function to make streamlit page"""
    load_dotenv()
    configuration = environ
    conn = get_db_connection(configuration)

    st.title("Subscription")
    st.metric("Subscribers", get_subscription_count(conn))
    with st.form(clear_on_submit=True, key="subscribe_form"):
        st.header("Mailing list")
        email = st.text_input("Enter your email - ")
        email_expression = r"((?:(?:[a-z0-9_-]+\.)?)+[a-z0-9_-]+@[a-z0-9_-]+\.[a-z]+(?:\.[a-z]+)?)"
        is_a_match = fullmatch(email_expression, email)
        if st.form_submit_button("Submit email"):
            try:
                if email.strip() == "":
                    st.error("Please fill in your email!")
                elif not is_a_match:
                    st.error("Please enter valid email!")
                else:
                    st.success("Email submitted!")
                    validated_email = is_a_match.group()
                    add_email_to_database(conn, validated_email)
            except Exception as err:
                print(err)
                return


if __name__ == "__main__":
    main()
