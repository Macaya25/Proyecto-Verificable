# Instrucciones para iniciar la aplicacion

## .Env
Para poder correr  el dockers, se tiene que crear un archivo .env dentro de la carpeta app.
En esta deben haber 2 variables
```
DATABASE_URI=mysql+pymysql://root:root@db:3306/db
SECRET_KEY = "clave_secreta"
```


## Iniciar Contenedores 
Para iniciar los contenedores solo tenemos que correr 

```sh
docker-compose up --build
```
