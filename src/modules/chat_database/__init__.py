# src/
# └── modules/
#     └── chat_database/
#         ├── __init__.py
#         │
#         ├── application/
#         │   ├── __init__.py
#         │   └── services.py
#         │
#         ├── domain/
#         │   ├── __init__.py
#         │   ├── entities.py
#         │   ├── interfaces.py
#         │   ├── value_objects.py
#         │   └── exceptions.py
#         │
#         ├── infrastructure/
#         │   ├── __init__.py
#         │   ├── database.py
#         │   ├── llm_sql_generator.py
#         │   ├── sql_validator.py
#         │   ├── postgres_executor.py
#         │   └── result_formatter.py
#         │
#         └── interfaces/
#             ├── __init__.py
#             ├── router.py
#             └── schemas.py