# Instrucciones para iniciar el contenedor

## .Env
Para poder correr  el dockers, se tiene que crear un archivo .env dentro de la carpeta app.
En esta debenr haber 2 variables
```
DATABASE_URI="mysql+pymysql://usuario:contraseña@ip_localhost:puerto/db"
SECRET_KEY = "clave_secreta"
```

## Comunas y regiones
Necesitamos descargar el archivo de regionesComunas.xlsx, que se encuentra en canvas, y copiarlo en la carpeta app.
Una vez iniciados los contenedores tenemos que ir al contenedor de app_1, ir al terminal y ejecutar el siguiente comando.

``` python seed.py ```



Ya listo, se puede probar el codigo.