import pandas as pd
from sqlalchemy import create_engine

# Configuración de la conexión a la base de datos
engine = create_engine('mysql+pymysql://root:Andres?250297@localhost/db')

# Leer los datos del archivo Excel
df_region = pd.read_excel('regionesComunas.xlsx', sheet_name='regiones')
df_comuna = pd.read_excel('regionesComunas.xlsx', sheet_name='comunas')

# Subir los datos a las tablas de la base de datos
with engine.connect() as connection:
    # Llenar la tabla Region
    df_region.to_sql('region', con=engine, if_exists='append', index=False)

    # Llenar la tabla Comuna
    df_comuna.to_sql('comuna', con=engine, if_exists='append', index=False)

    # Insertar datos en la tabla CNE
    cne_data = [
        {'id': 8, 'descripcion': 'Compraventa'},
        {'id': 99, 'descripcion': 'Regularización de Patrimonio'}
    ]
    for entry in cne_data:
        query = f"INSERT INTO cne (id, descripcion) VALUES ({entry['id']}, '{entry['descripcion']}')"
        connection.execute(query)

print("Tablas rellenadas con éxito.")
