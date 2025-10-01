import os
from contextlib import contextmanager

try:
    import pymysql
    from pymysql.cursors import DictCursor
except Exception as e:  # pragma: no cover
    pymysql = None
    DictCursor = None


def _load_dotenv_simple():
    """Carga un archivo .env simple (KEY=VALUE por línea) si existe.
    No requiere la librería python-dotenv.
    Solo define variables que no estén ya presentes en el entorno.
    """
    # Directorios candidatos: CWD, CWD/db, raíz del proyecto (padre de Modulos), raiz/db
    base_from_module = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    candidates = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), 'db', '.env'),
        os.path.join(base_from_module, '.env'),
        os.path.join(base_from_module, 'db', '.env'),
    ]
    seen = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            # Preferir valores del archivo .env si no hay valor ya en entorno
                            if k and (k not in os.environ or os.environ.get(k) == ''):
                                os.environ[k] = v
            except Exception:
                # No romper si hay errores de lectura del .env
                pass


# Intentar cargar .env antes de leer los parámetros
_load_dotenv_simple()


def _get_db_params():
    """Obtiene parámetros de conexión desde variables de entorno.

    Variables soportadas (con valores por defecto):
    - DB_HOST (default: localhost)
    - DB_PORT (default: 3306)
    - DB_USER (default: junior)
    - DB_PASS (default: "Junior0719")
    - DB_NAME (default: sistemaPy)
    """
    return {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', '3306')),
        'user': os.environ.get('DB_USER', 'junior'),
        'password': os.environ.get('DB_PASS', 'Junior0719'),
        'database': os.environ.get('DB_NAME', 'sistemaPy'),
        'charset': 'utf8mb4',
        'cursorclass': DictCursor,
        'autocommit': False,
    }


def _check_driver():
    if pymysql is None:
        raise RuntimeError(
            "PyMySQL no está instalado. Instala con: pip install pymysql"
        )


def get_connection():
    """Crea y retorna una conexión nueva a MariaDB/MySQL."""
    _check_driver()
    params = _get_db_params()
    try:
        return pymysql.connect(**params)
    except Exception as e:
        # Re-lanzar con contexto para facilitar diagnóstico (usuario/host/db)
        raise RuntimeError(
            f"Error conectando a DB: {e} | user={params.get('user')} host={params.get('host')} "
            f"db={params.get('database')} (configure con DB_HOST/DB_PORT/DB_USER/DB_PASS/DB_NAME o .env)"
        ) from e


@contextmanager
def transaction():
    """Contexto de transacción: hace commit si todo va bien, rollback si no."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def fetch_all(sql: str, params=None):
    """Ejecuta SELECT y retorna lista de dicts."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def fetch_one(sql: str, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def execute(sql: str, params=None):
    with transaction() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.lastrowid
