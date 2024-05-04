import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey

# Conexión a la base de datos MySQL
# Reemplaza 'username', 'password', 'hostname', 'database_name' con tus credenciales
engine = create_engine('mysql+pymysql://root:Andres?250297@localhost/db')
connection = engine.connect()
metadata = MetaData()

# Lectura de las hojas del archivo Excel
df_regiones = pd.read_excel('regionesComunas.xlsx', sheet_name='regiones')
df_comunas = pd.read_excel('regionesComunas.xlsx', sheet_name='comunas')
df_cne_elements = pd.DataFrame({
    'id': [99, 8],
    'descripcion': ['Regularizacion de Patrimonio', 'Compraventa']
})

# Renombrar las columnas para que coincidan con los nombres en la base de datos
df_regiones.rename(columns={'id_region': 'id'}, inplace=True)
df_comunas.rename(columns={'id_comuna': 'id'}, inplace=True)

# Subida de los datos a las tablas
df_regiones.to_sql('region', con=engine, if_exists='append', index=False)
df_comunas.to_sql('comuna', con=engine, if_exists='append', index=False)
df_cne_elements.to_sql('cne', con=engine, if_exists='append', index=False)

print("Tablas y relaciones creadas con éxito en la base de datos MySQL")
