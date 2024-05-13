# Instrucciones para iniciar la aplicacion

## .Env
Para poder correr  el dockers, se tiene que crear un archivo .env dentro de la carpeta app.
En esta deben haber 2 variables
```
DATABASE_URI=mysql+pymysql://root:root@db:3306/db
SECRET_KEY = "clave_secreta"
```

## Comunas y regiones


## Iniciar Contenedores y, poblar comunas y regiones.
Para iniciar los contenedores solo tenemos que correr 

```sh
docker-compose up --build
```

Una vez iniciados los contenedores tenemos que ir al contenedor de app_1, ir al terminal y ejecutar el siguiente comando.

```sh
python seed.py
```

Con esto tenemos las comunas y regiones en la db.

