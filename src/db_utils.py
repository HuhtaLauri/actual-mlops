from contextlib import contextmanager
import psycopg


@contextmanager
def cursor(connection_string: str, commit: bool = False):
    conn = psycopg.connect(connection_string, autocommit=False)

    try:
        cur = conn.cursor()
        yield cur
    except psycopg.Error as e:
        print(e)
    finally:
        if commit:
            conn.commit()
        conn.close()
