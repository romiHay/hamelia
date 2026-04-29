from app.database import SESSION, MY_ENGINE, Base
from sqlalchemy import text


def init_db():
   db = SESSION()
   try:
       # 1. Create schemas if they don't exist
       print("Ensuring schemas exist...")
       db.execute(text("CREATE SCHEMA IF NOT EXISTS web_general"))
       db.execute(text("CREATE SCHEMA IF NOT EXISTS missions"))
       db.commit()

       # 2. Create tables
       print("Ensuring tables exist...")
       Base.metadata.create_all(bind=MY_ENGINE)

       # 3. Create/Update the trigger function
       print("Ensuring update trigger function exists...")
       db.execute(text("""
           CREATE OR REPLACE FUNCTION update_updated_at_column()
           RETURNS TRIGGER AS $$
           BEGIN
               NEW.updated_at = CURRENT_TIMESTAMP;
               RETURN NEW;
           END;
           $$ language 'plpgsql';
       """))

       # 4. Apply triggers to core tables
       tables = [
           ('web_general', 'users'),
           ('web_general', 'teams'),
           ('web_general', 'missions_data'),
           ('web_general', 'geometries'),
           ('web_general', 'mission_assets'),
           ('missions', 'rules')
       ]

       for schema, table in tables:
           # Check if trigger already exists (PostgreSQL specific)
           trigger_exists = db.execute(text(f"""
               SELECT 1 FROM pg_trigger
               WHERE tgname = 'update_{table}_modtime'
           """)).scalar()

           if not trigger_exists:
               print(f"Creating trigger for {schema}.{table}...")
               db.execute(text(f"""
                   CREATE TRIGGER "update_{table}_modtime"
                   BEFORE UPDATE ON "{schema}"."{table}"
                   FOR EACH ROW
                   EXECUTE FUNCTION update_updated_at_column();
               """))
       db.commit()
       print("Database initialization complete.")

   except Exception as e:
       print(f"Database initialization ERROR: {e}")
       db.rollback()
   finally:
       db.close()
