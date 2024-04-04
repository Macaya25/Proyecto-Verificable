Para poder correr  el dockers, se tiene que crear un archivo .env dentro de la carpeta app.
En esta debenr haber 2 variables

DATABASE_URI="mysql+pymysql://usuario:contraseña@ip_localhost:puerto/db"
SECRET_KEY = "clave_secreta"

Se corre, por lo general se sube primero el container de db y luego el de app pero da un error el de app, hay que volver a lanzar solo el de app y funciona.
Luego, para poblar las comunas se tiene que correr el comunas.py y el archivo de  comunas está en el canvas, hay que descargarlo y agregarlo al directorio.
# No olvidar
Se tiene que poblar el cne en la base de datos para que aparezcan, estan compuesto por un id que se genera solo y una descripcion que es le nombre del cne compra y venta ej.
el primero que creas tiene que ser compra y venta y el segundo regularización del patrimonio
