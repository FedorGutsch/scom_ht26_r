import pandas as pd
import json
import ast
from app.database.session import SessionLocal, engine 
from app.schemas.candidate_base import Candidate
from app.schemas.vacancy_base import Vacancy

from app.database.base import Base

def _fix_list(val):
    """
    Парсит поле-список из CSV.
    Поддерживает:
    - '["a", "b"]' (JSON)
    - "['a', 'b']" (Python literal)
    - "a, b, c" (CSV-строка)
    - "" / None / [] → []
    """
    # 1. Пустые значения
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if isinstance(val, list):
        return val  # уже список → возвращаем как есть
    
    # 2. Строка → чистим
    if not isinstance(val, str):
        return []
    val = val.strip()
    if val in ('[]', '""', "''", ''):
        return []
    
    # 3. Пробуем JSON
    if val.startswith('['):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            pass
    
    # 4. Пробуем Python literal (ast)
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, list):
            return parsed
    except (ValueError, SyntaxError):
        pass
    
    # 5. Фоллбэк: просто сплит по запятой (твой случай)
    return [x.strip() for x in val.split(',') if x.strip()]

def read_csv_safe(file_path: str, delimiter: str = ','):
    for enc in ['utf-8-sig', 'utf-8', 'cp1251', 'latin1']:
        try:
            df = pd.read_csv(file_path, delimiter=delimiter, encoding=enc)
            print(f"🔓 Кодировка: {enc}")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"❌ {file_path} не читается.")

def _fix_json(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if not isinstance(val, str):
        return val
    val = val.strip()
    if val in ('[]', '""', "''", ''):
        return []
    try:
        return json.loads(val)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return []

def load_csv(file: str, model, list_cols: list[str] | None = None, delimiter: str = ','):
    print(f"⏳ Читаю {file}...")
    df = read_csv_safe(file, delimiter)

    # Парсим списки (skills, actions_history)
    if list_cols:
        for col in list_cols:
            if col in df.columns:
                df[col] = df[col].apply(_fix_list)

    # Парсим даты
    date_cols = [c for c in df.columns if '_at' in c or c in ('created_at', 'updated_at', 'time', 'date')]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    records = df.to_dict(orient="records")
    
    # Чистим NaN/None
    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if v is None: continue
            if isinstance(v, float) and pd.isna(v): continue
            clean_row[k] = v
        cleaned.append(clean_row)

    db = SessionLocal()
    try:
        db.add_all([model(**row) for row in cleaned])
        db.commit()
        print(f"✅ {file}: {len(cleaned)} строк залито.")
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка БД: {e}")
        raise
    finally:
        db.close()
        
if __name__ == "__main__":
    print("🚀 Запуск импорта...")
    
    # 👇 СОЗДАЁМ ТАБЛИЦЫ ПЕРЕД ИМПОРТОМ (критично для пустой БД)
    Base.metadata.create_all(bind=engine)
    print("🚀 Запуск импорта...")
    # Укажи свои пути к CSV
    load_csv("scripts/cand.csv", Candidate, list_cols=["skills", "actions_history"])
    load_csv("scripts/vac.csv", Vacancy, delimiter=';')
    print("🏁 Готово. База заполнена.")