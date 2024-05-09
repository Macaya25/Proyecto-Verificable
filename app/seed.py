import pandas as pd
from sqlalchemy import create_engine, MetaData

engine = create_engine('mysql+pymysql://root:root@db:3306/db')
connection = engine.connect()
metadata = MetaData()

df_regiones = pd.read_excel('regionesComunas.xlsx', sheet_name='regiones')
df_comunas = pd.read_excel('regionesComunas.xlsx', sheet_name='comunas')
df_cne_elements = pd.DataFrame({
    'id': [99, 8],
    'descripcion': ['Regularizacion de Patrimonio', 'Compraventa']
})

df_regiones.rename(columns={'id_region': 'id'}, inplace=True)
df_comunas.rename(columns={'id_comuna': 'id'}, inplace=True)

df_regiones.to_sql('region', con=engine, if_exists='append', index=False)
df_comunas.to_sql('comuna', con=engine, if_exists='append', index=False)
df_cne_elements.to_sql('cne', con=engine, if_exists='append', index=False)

print("Tablas y relaciones creadas con éxito en la base de datos MySQL")
