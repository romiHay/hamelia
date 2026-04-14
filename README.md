# hamelia

### db_models explanation
#### Layer 1: The Pydantic Model - The "Form Checker"
File: app/pydantic_schemas.py (RuleCreate, GeometryCreate)\
Role: This is the Validation Layer. It is just a "schema."\
What happens: When your frontend sends a JSON package, FastAPI looks at your Pydantic model and says: "Does this look correct? Is the Name a string? Is the Type a Point?"\
Result: It turns the raw JSON into a Python object called data. This data lives in your RAM (memory) only for a second. It is NOT connected to the database.

#### Layer 2: The Logic - The "Bridge"
File: Your router file - can either be geometries or rules
Role: This is where you decide what to do with the "checked form" from Layer 1.\
The Connection:
1. You take the validated data (Pydantic model).
2. You ask the database for the corresponding row: db.query(GeometryRow).filter(...).
3. The Link: You copy the values from the Pydantic model into the DB Row: geo_row.geometry_name = geo.name etc.

#### Layer 3: The DB Models - The "Database Mirror"
File: app/db_models.py (GeometryRow, GenericRuleRow)\
Role: This is the Persistence Layer.\
What happens: These classes are mapped directly to your actual SQL database tables.
Persistence: When you write db.commit(), SQLAlchemy looks at all the GeometryRow objects you touched in Layer 2 and sends the actual SQL commands to save them permanently to the disk.
##### How the "Filter" works:
When you write: db.query(GeometryRow).filter(GeometryRow.uuid == geo.id) for example\
SQLAlchemy does these steps behind the scenes:
1. Look at the Class: "Oh, they used GeometryRow. Let me check my Map..."
2. Find the Table: "The Map says GeometryRow belongs to the table geometries."
3. Look at the Connection: "I'm using the db session, which is connected to the file mission_control.db."
4. Translate to SQL: It converts your Python code into actual SQL: SELECT * FROM geometries WHERE uuid = '...'
5. Send the Command: It sends that command to the database, gets the data, and wraps it back into a Python object for you.
