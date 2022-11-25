# Proyecto 2 Journal Search Platform (JSP) 
    Instituto Tecnológico de Costa Rica
    Escuela de Ingeniería en Computación 
    IC-4302 Bases de Datos II
    Prof. Nereo Campos
    IIS 2022

## Integrantes

    Johnny Díaz Coto         - 2020042119
    Pamela González López    - 2019390545
    Andrea Li Hernández      - 2021028783
    Deyan Sanabria Fallas    - 2021046131
    Andrés Sánchez Rojas     - 2018100180

## Instrucciones de como ejecutar el proyecto
El proyecto se encuentra en un repositorio privado de GitHub, el profesor del curso o las personas permitidas pueden realizar la instalación sin ningún problema, en el caso de personas fuera del repositorio, en caso de cambiarse la configuración de este también podrían hacer las mismas cosas que se explicaran a continuación.

### Clonación del Repositorio
Para poder clonar los documentos que se encuentran en GitHub se debe realizar el siguiente comando:

```bash
git clone https://github.com/jonkox/Journal-Search-Platform-JSP.git
```
Esto lo que hará es descargar el proyecto dentro de la computadora que lo ejecute. Es recomendable tener una cuenta de GitHub para evitar algunos problemas con la autenticación.
Hecho este paso debe obtener el proyecto con una distribución así:

<div style="text-align: center;"><img src=https://i.imgur.com/f1UxzHZ.png
></div>

El proyecto se constituye de varias carpetas, cada una de ellas tiene su función, sin embargo se pueden dividir en dos grupos, estos son:
* Helm Charts
    * application
    * databases
    * monitoring
* Aplicaciones
    * Images
        * API
        * Details Downloader
        * Downloader
        * Jatsxml Processor
        * Loader
    * Pruebas

Las aplicaciones contienen todo el código necesario para ejecutar la tarea que cada una de ellas debe de cumplir, estas se dividen en el código de producción y la rama de pruebas.
Por otro lado, los Helm Charts son utilizados para instalar todas las herramientas dentro de Kubernetes, donde cada Helm Chart instala distintas herramientas de la siguiente manera:

* application
    * Instala todas las aplicaciones creadas por el equipo de trabajo.
* databases
    * Instala las bases de datos que se necesitan en el proyecto, ElasticSearch y MariaDB y RabbitMQ.
* monitoring
    * Instala todas las herramientas de monitoreo del proyecto: prometheus y grafana.

### Pasos de Instalación
1. Posicionarse en la carpeta principal del proyecto.
2. Ejecutar el comando:
```bash!
helm install [name][chart]
```
En nuestro caso serían los siguientes comandos:
```bash!
helm install databases databases
helm install monitoring monitoring
helm install application application
```
### Nota
Al crear un Helm Chart e instalarlo, se va a utilizar el nombre del chart seguido por el nombre del componente en cuestión, *[nombre del chart]-[nombre del componente]*. En nuestro caso por ejemplo, con el Helm Chart encargado del monitoreo tiene como nombre “monitoring”, así que un ejemplo práctico del nombre de un pod es **monitoring-mariadb**, dónde esto lo podemos saber con anticipación gracias al nombre del chart y el componente que se desea instalar.
Ahora, esto nos afecta directamente en distintas situaciones, dónde continuando con el ejemplo de monitoring:
* En el momento de obtener la contraseña de MariaDB por medio de variables de entorno se tiene la siguiente sección dentro del deployment:
```yaml
- name: "MARIADBPASS"
  valueFrom:
  secretKeyRef:
    name: databases-mariadb
    key: mariadb-root-password
    optional: false
```
Al momento de escribir el código necesario para esta tarea se tiene en cuenta los nombres de los componente para así conocer desde antes su valor, por tanto, es importante tener en cuenta el nombre de los charts al momento de su creación y programación a sus al rededores.

## Ejecución del proyecto
### Thunkable
Para esta aplicación se debe estar registrado previamente en Thunkable. Usted puede crear una copia ([link](https://x.thunkable.com/copy/5cb946033e762160fac98bdb6402d2e9)) con la cual puede trabajar.
Una vez con su copia puede ejecutar el proyecto desde su computador o desde un dispositivo móvil como un celular o tablet.

* Versión Web
    De esta manera, una vez en el proyecto en la sección superior derecha se puede encontrar la siguiente barra de herramientas.
<div style="text-align: center;"><img src=https://i.imgur.com/VPVSxi6.png></div>

con ella se pueden realizar las distintas acciones para ejecutar la aplicación, el componente de más a la izquierda con un dibujo de `play` consta de la prueba de una versión web de la aplicación, la cual mostrara algo similar a la siguiente imagen:
<div style="text-align: center;"><img src=https://i.imgur.com/jBC9sKA.png></div>


De este modo podrá realizar las distintas opciones que la aplicación posee.

* Versión Móvil
    Como se puede observar en la imagen anterior, la misma página oficial de recomienda el uso de la aplicación móvil, pues, es una aplicación móvil, lo mejor sería probarla en un dispositivo móvil como tal. 
    Para ello se necesita tener instalado en el dispositivo la aplicación de Thunkable.
<div style="text-align: center;"><img src=https://i.imgur.com/q6ytEnu.png width="200" height="400"></div>
    
Para lograr la prueba móvil se debe seleccionar la opción de *live test on device* y entrar a la aplicación de Thunkable Live en el dispositivo móvil.

### Thunkable live

En la web de Thukable después de haber seleccionado la opción de *live test on device* debe iniciar su aplicación de Thunkable Live donde vera algo similar a lo siguiente:

<div style="text-align: center;"><img src=https://i.imgur.com/q2IXlLK.png height="400"></div>

Debe seleccionar su proyecto, en este caso es el proyecto de Proyecto#2_JSP. A partir de este punto el usuario se encuentra en libertad de probar cada una de las funcionalidades de la app. 

### Ngrok
Para utilizar esta herramienta se debe descargar dentro del computador, esto se puede realizar de una forma muy sencilla en caso de tener las herramientas necesarias para su instalación se puede usar los comandos:

#### Windows
```bash
choco install ngrok
```

#### Mac
```bash
brew install ngrok/ngrok/ngrok
```

En caso de no contar con las de Chocolatey o Hombrew de igual manera se puede descargar el en un formato comprimido para su instalador.

Una vez terminada su descarga, dentro de la página oficial de [ngrok](https://ngrok.com/) se debe crear una cuenta, seguidamente debe obtener el `token` de autenticación para sincronizarlo en su aplicación local, para ello se ejecuta el comando:
```bash
ngrok config add-authtoken <token>
```
Donde el `<token>` es distinto de cada usuario.
Una vez realizado este paso, ngrok está listo para funcionar y esto se logra con el siguiente comando:

```bash
ngrok http <port>
```
Donde `<port>` se refiere al puerto donde se creará el túnel para la comunicación entre las dos partes, la aplicación de Thunkable y el API. (por defecto es 5000)

### Abrir puertos del API
Antes de ejecutar ngrok o la app, se necesita ejecutar el siguiente comando en una terminal:
```bash
kubectl port-forward SERVICE/api-service <puerto-deseado>:5000
```
Donde \<puerto-deseado\> es el puerto donde se hosteara localmente el API, este puerto es necesario para el siguiente paso.

### Ejecutar Ngrok
Una vez expuesto el API, con la herramienta de Ngrok se va a exponer al API a "el resto del mundo", lo que va a generar un túnel entre el API y el Internet. Para lograr esto de buena manera debe tener en cuenta el puerto elegido en el paso anterior, en este ejemplo, el puerto es 63456, por lo que se ejecuta el siguiente comando:

```shell
ngrok [protocolo] [puerto]
```
Tomando en cuenta este ejemplo en concreto, el comando que se necesita ejecutar es el siguiente:

```bash
ngrok http 63456
```
Debe obtener un resultado parecido al siguiente:
<div style="text-align: center;"><img src=https://i.imgur.com/WtGhdlo.png></div>


De nuevo, note el recuadro amarillo, pues este indica el URL al cual puede acceder al API de forma pública, así de esta manera la app se puede comunicar con el API.

---
### Thunkable

<div style="text-align: center;"><img src=https://i.imgur.com/CfmuElZ.png></div>

En esa seccion hay que colocar el URL obtenido anteriormente en Ngrok.

Una vez realizado todo lo anterior, solo queda utilizar la APP, para un ejemplo, ir a las [pruebas generales](#pruebas-generales)



---
## Explicación de Secciones Varias
### Observabilidad con Grafana
#### Codigos de las plantillas para Grafana:
> Elasticsearch: 14191
> MariaDB: 13106
> Rabbit: 10991

#### Aplicar plantillas con codigos
Para aplicar las plantillas anteriores, hay que primero, ingresar a grafana, ir al icono de cuatro cuadrados y presionar import como en la siguiente imagen:
<div style="text-align: center;"><img src=https://i.imgur.com/xuk9yTB.png></div>

Una vez en ese lugar, colocar uno de los anteriores y presionar load:
<div style="text-align: center;"><img src=https://i.imgur.com/ckPs0iP.png></div>

Por ultimo presionar el boton que dice import:
<div style="text-align: center;"><img src=https://i.imgur.com/yrZRP23.png></div>

Repetir los pasos con cada codigo.

#### Importar plantilla de la App desarrollada
La plantilla de la app desarrollada se importa de una forma parecida, despues del segundo paso hay que hacer lo siguiente, pulsar en el boton que dice "Upload JSON file":
<div style="text-align: center;"><img src=https://i.imgur.com/vPgsXn8.png></div>

Una vez hecho eso, seleccionar el json llamado "dashboard.json" ubicado en la raiz de este proyecto y abrirlo:
<div style="text-align: center;"><img src=https://i.imgur.com/3GDC3ck.png></div>

Por ultimo, presionar importar:
<div style="text-align: center;"><img src=https://i.imgur.com/xT8LlWG.png></div>




### Values de Application
El archivo values.yaml que se puede encontrar en la carpeta ./application contiene la información que necesitan componentes como ElasticSearch, RabbitMQ, MariaDB. Para estos se tienen valores **generales** que debe utilizar cada aplicación del sistema, estas son:

    Host: Dirección del proveedor.
    Port: Puerto de conexión.
    User: Usuario con el cual brinda el acceso al servicio.
    
Lo que podemos encontrar dentro del archivo es:
```yaml
general:
  # Elastic
  elastichost: "http://databases-elasticsearch-master-hl.default.svc.cluster.local"
  elasticport: 9200
  elasticuser: "elastic"
  elasticindex: "registries"

  # RabbitMQ
  rabbithost: "databases-rabbitmq-headless"
  rabbitport: 5672
  rabbituser: "user"

  # Mariadb
  mariadbname: "my_database"
  mariadbhost: "databases-mariadb-primary"
  mariadbport: 3306
  mariadbuser: "root"
  apiurl: "https://api.biorxiv.org/"
```

Ahora, con los componentes creados por el equipo se tienen valores para cada uno de ellos, estos consisten en: cantidad de réplicas y nombre de la cola de RabbitMQ en caso de ser necesario. Un ejemplo práctico sería el siguiente caso:

```yaml
loader:
  queuename: "loader"
  sleeptime: 1
  replicas: 3
  metrics: 6943
```
Al final este archivo nos ayuda en la configuración de cada uno de los componentes y especificar la cantidad de réplicas que se desean de cierto componente.



### NodePorts
Los servicios de tipo NodePort nos permiten comunicar componentes dentro del cluster de Kubernetes con los componentes fuera de este ambiente, esto es muy funcional para poder visualizar distintos puntos desde aplicaciones terceras o tener la seguridad de un host y port donde vamos a poder consultar por datos.
Para poder crear un servicio de tipo NodePort se tienen dos opciones, crear un servicio mediante un archivo yaml o mediante la configuración en el values dentro del Helm chart correspondiente. En nuestro grupo de trabajo se escogió la segunda opción.

Esto se ve de la siguiente manera dentro del values del Helm Chart databases:

```yaml
kibana:
  service:
    type: NodePort
    nodePorts:
      http: 31500
```
Este es un ejemplo de los varios que hay dentro del documento, en este caso, Kibana. Para poder crear este servicio se necesita:
* Especificar el servicio.
* Especificar el tipo de servicio, en este caso NodePort.
* Especificar el puerto a exponer, en este caso fue el 31500. Los puertos deben estar dentro de un rango de **[30000,32767]**.

Dentro del proyecto todos los componentes de monitoring y databases tienen sus propios NodePorts para un mejor manejo durante la etapa de desarrollo, sin embargo, si el usuario desea seguir con el clásico ClusterIP se debe cambiar simplemente el tipo de servicio.

    type: NodePort  --> type: ClusterIP



### Recursos
Limitación de recursos, la elaboración del proyecto fue un poco difícil ya que todos los integrantes no poseen la facilidad de un equipo con los recursos suficientes para poder levantar todos los componentes que se necesitaban dentro del proyecto, es por eso que se optó por ciertas opciones que ayudaban a reducir el consumo de memoria, una de las soluciones para este tipo de situaciones es la limitación de los componentes, en términos generales esto consiste en darle valores máximos de uso de los recursos a cada una de las aplicaciones que se encuentran corriendo, lo que nos ayuda a la reducción general del uso de memoria.

Para cada componente que se quiera limitar se sigue una plantilla general:


```yaml
resources:
  limits: 
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 128Mi
```
Donde los valores ingresados son medidos por:
* m  --> milésima de núcleo (thousandth of a core)
* Mi --> Mibibyte

De esta menera se puede ir por cada componente hasta llegar un balance del consumo de recursos en de uso y de request para un mejor rendimiento.

---
## Contraseñas
Los componentes de ElasticSearch, MariaDB y RabbitMQ poseen sus contraseñas, en nuestro equipo de trabajo no se vio necesaria la estipulación de contraseñas definidas, sino que, por el contrario, cada uno de los componentes genera su propio usuario y contraseña. A raíz de esta situación es que antes de realizar alguna de las pruebas que se documentan en esta sección debe tener presente esto.
Al momento de instalar los componentes debe recuperar las contraseñas e insertarlas en los espacios correspondientes, para esto se deben seguir los siguientes pasos:
* Utilizar la aplicación Lens para una mejor comodidad.
* Navegar a la conexión del cluster, en la sección "Config" se encuentra un espacio de nombre "Secrets".
<div style="text-align: center;"><img src=https://i.imgur.com/m21RV98.png></div>
* Una vez en esta sección se pueden ver todos los secrets de todos los componentes, así que de esta menera podemos seleccionar el componente en cuestión, obtener sus información de acceso y sustituirlo en los archivos de prueba que se mencionan en las secciones siguientes.

Para continuar con el ejemplo, se obtendrá la contraseña de ElasticSearch, esta se puede encontrar seleccionando el componente en la sección de secrets vista, por lo que se obtiene lo siguiente:
<div style="text-align: center;"><img src=https://i.imgur.com/PyrtXYq.png></div>

La contraseña encontrada se escribirá dentro del espacio correspondiende en el archivo de pruebas como se ve a continuación:
<div style="text-align: center;"><img src=https://i.imgur.com/FlsPkHK.png></div>

Note la línea azul de la izquierda, en ese punto es dónde se ha inscrito la contraseña.

Debe tener esto en cuenta antes de replicar cada una de las pruebas que en este documento se detallan.

### NOTA
Al momento de realizar la instalación de cada uno de los componentes crea un *Persistant Volume Claim* (PVC) y un *Persistant Volume* (PV) dónde se guarda la información que contienen en ese momento de manera persistente, al momento de desinstalar los componentes estas secciones no se eliminan, es por eso que si al reinstalar los componentes y realizar los pasos anteriores no funcionan, asegúrese de haber eliminado previamente los PVC y PV antes de volver a instalar los componentes, pues la información de la contraseña que se está mostrando no es la correcta, ya que se muestra la contraseña actual, pero los componentes están tomando como contraseña la que dice el PVC y el PV, que son de instalaciones previas.
Con la ayuda de Lens es muy fácil realizar este proceso con los siguientes pasos:
* En la sección de Storage, seleccionar el espacio de PVC.
* Seleccionar los elementos a eliminar.
* Eliminarlos.

<div style="text-align: center;"><img src=https://i.imgur.com/JJ2q8P2.png></div>

## Pruebas realizadas

## Pruebas Generales

Para la ejecución de las pruebas generales se necesita tener todos los componentes previamente instalados.
Con el comando
```bash
kubectl get pods
```
Si los pasos de instalación fueron ejecutados correctamente se debe obtener el siguiente resultado:
<div style="text-align: center;"><img src=https://i.imgur.com/tuXeQqR.png
></div>

Esto indica que se tienen todos los componentes del proyecto instalados de buena manera y funcionando.

Despues hay que realizar los pasos para la ejecucion del proyecto que se encuentra en la seccion [Ejecución del proyecto](#ejecución-del-proyecto)

Una vez con todos los componentes instalados de buena manera y se realizaron los pasos para la ejecucion del proyecto, se procede con la prueba general de funcionamiento:

### Prueba del Pipeline:
Para probar el pipeline se necesita crear un job, esto se hace de la siguiente manera. En el app se inicia sesion (se registra previamente):

<div style="text-align: center;"><img src=https://i.imgur.com/QStvnnF.png></div>

Luego hay que seleccionar la opcion "Crear job":

<div style="text-align: center;"><img src=https://i.imgur.com/Zuq4kMP.png></div>

Por ultimo, colocar un valor para el tamaño de los grupos y presionar en crear:
<div style="text-align: center;"><img src=https://i.imgur.com/kqlSyUt.png></div>

#### Resultados:
Esto procede a crear un job en mariaDB de la siguiente manera:
<div style="text-align: center;"><img src=https://i.imgur.com/CW0aP2B.png></div>

El loader crea los grupos y los demas componentes empiezan a trabajar sobre ellos:
<div style="text-align: center;"><img src=https://i.imgur.com/WSvnryk.png></div>
<div style="text-align: center;"><img src=https://i.imgur.com/4OL8zsl.png></div>

En la tabla history se empieza a reflejar los procesos que realizan los pods:
<div style="text-align: center;"><img src=https://i.imgur.com/pHUqYcx.png></div>

Se crea un indice donde se guardan los documentos con el nombre especificado en el values.yaml:
<div style="text-align: center;"><img src=https://i.imgur.com/DWo4MMU.png></div>

En el indice de groups se puede ver como van bajando la cantidad de groups en el indice:
<div style="text-align: center;"><img src=https://i.imgur.com/4XVu5cd.png></div>

En las colas de RabbitMQ se puede ver como trabajan:
<div style="text-align: center;"><img src=https://i.imgur.com/QsGEglO.png></div>

### Pruebas de busquedas en la App:
Para probar las busquedas en la app ahora se debe elegir la opcion de "Buscar artículo":
<div style="text-align: center;"><img src=https://i.imgur.com/avH3L0P.png></div>

Sera presentado con la siguiente pantalla, solo queda colocar algo para buscar, ya sea nombre de autores, fechas, titulos, etc. y presionar "Buscar":
<div style="text-align: center;"><img src=https://i.imgur.com/2sY80tS.png></div>

#### Resultados
Buscar "covid" da los siguientes resultados:
<div style="text-align: center;"><img src=https://i.imgur.com/4UMbx6P.png></div>

Buscar "2011" da los siguientes resultados:
<div style="text-align: center;"><img src=https://i.imgur.com/pdGhja7.png></div>

Buscar "issue" da los siguientes resultados:
<div style="text-align: center;"><img src=https://i.imgur.com/hvsXLQS.png></div>

### Prueba articulos guardados:
Estando en la lista de resultados de la prueba anterior, se puede presionar un articulo y se le presenta lo siguiente:
<div style="text-align: center;"><img src=https://i.imgur.com/pkKgRS6.png></div>

Al dar like pasa lo siguiente:
<div style="text-align: center;"><img src=https://i.imgur.com/5niH5DJ.png></div>

Ahora eligiendo la opcion "Ver artículos guardados" en el menu de opciones podra ver los articulos que guardo:
<div style="text-align: center;"><img src=https://i.imgur.com/shfBT1e.png></div>

#### Resultados:
Se tienen los siguientes articulos guardados:
<div style="text-align: center;"><img src=https://i.imgur.com/tFr7F1Q.png></div>

Presionar alguno, despliega lo siguiente:
<div style="text-align: center;"><img src=https://i.imgur.com/dAczB8b.png></div>

---
## Pruebas unitarias y resultados de estas.

### Pruebas Unitarias de **Loader**
Este componente es el encargado de crear la cantidad de grupos especificada por un tamaño de grupo. Este componente recibe un conjunto de datos conocido como *Job* el cual contiene los datos necesarios para el procesamiento del mismo.

Los Jobs se guardan en una base de datos destinada para ellos la cual es MariaDB y se guardan de la siguiente manera:
<div style="text-align: center;"><img src=https://i.imgur.com/OdhtSKd.png></div>

El trabajo real del Loader se consta en:
* tomar uno a uno cada Job para ser procesado, para esto se obtiene 1 registro de los Jobs que se encuentren en estado de 'NEW'. 
* Una vez obtenido este registro se obtiene el tamaño del grupo para, obtener la cantidad de grupos que se deben realizar.
* Crear la cantidad de grupos que se necesitan.
* Actualizar en la tabla Jobs, el Job tomado debe tener su estado a 'IN-PROGRESS' y el campo Loader con el ID del pod que lo ha procesado.
* Enviar mensaje a una cola de RabbitMQ para que el siguiente componente reciba la información de los grupos que han sido procesados y creados.


Como prueba unitaria, se encuentra un archivo de prueba llamado unitTest.py en el directorio ‘. \Images\Loader\UnitTest'

Este archivo funciona de manera similar al código de producción, sin embargo, contiene dos diferencias principales:
1. En esta prueba unitaria se tiene un ciclo FOR como principal para el procesamiento de los Jobs sea finito, pues el objetivo es ejemplificar el funcionamiento del mismo. El código de producción trabaja con un ciclo infinito de un WHILE True.
2. Esta prueba unitaria no crea las colas ni envía mensajes, pues todo lo que pasa lo muestra en consola.

Para ejecutar este archivo debe tener presente lo siguiente:
* Actualizar la contraseña de MariaDB
* Modificar variables de control como el sleeptime o la cantidad de Jobs para la prueba.


Primeramente, el programa inserta Jobs de prueba en una base de datos de prueba respectiva para su función y se obtienen datos similares a los siguientes:
<div style="text-align: center;"><img src=https://i.imgur.com/i6QJI2x.png></div>


Seguidamente el programa toma 1 Job para su procesamiento, el cual consiste en tomar el grp_size y el total de documentos del api de BioRxiv para saber la cantidad de grupos que se tienen que crear para ese Job en específico. A partir de este punto, se puede ver el funcionamiento del programa en la creación de los grupos, la información se muestra en consola de la siguiente manera:
<div style="text-align: center;"><img src=https://i.imgur.com/kltvo3P.png></div>


El programa ha tomado el Job con ID = 1 para ser procesado, pues es el primero que se ha encontrado con el estado de 'NEW', indicando que aún falta por ser procesado.
Una vez tomado se procesan todos sus grupos, en el momento de la ejecución de esta prueba, el sitio de BioRxiv contiene 25609 registros, así que para la cantidad de grupos que se necesitan se obtiene con la división de 25609/1338 dando como resultado 19.14, lo que nos indica que se necesitan **20** grupos, pues se van a lograr realizar 19 grupos de 1338 documentos y los que sobran van en el último grupo que guarda los restantes, es por eso que va de 0 hasta 19 grupos.


El procesamiento se ve reflejado en MariaDB de la siguiente manera:

<div style="text-align: center;"><img src=https://i.imgur.com/88TZVHD.png></div>
Estos han sido los grupos que se han insertado con los siguientes datos:
* id_job: Job al que pertenece el grupo.
* created: Indica el momento en que se creó el grupo.
* end: momento de finalización.
* stage: componente que lo está trabajando, en este caso, Loader.
* grp_number: el número del grupo.
* status: estado en que se encuentra el grupo, al ser la primera vez que se crea, este comienza en null.
* offset: cantidad del desplazamiento sobre los documentos.

También, en el momento que se toma el Job para su procesamiento, se modifica su estado a 'In-Progress' y su campo 'loader' se actualiza con el nombre del pod que ha tomado ese job, en este caso es un nombre genérico al ser una prueba unitaria, por lo que después del procesamiento de cada uno de los distintos Jobs de prueba se obtiene una tabla similar a:


<div style="text-align: center;"><img src=https://i.imgur.com/LwBHAgi.png></div>



### Prueba unitaria del **Downloader**

Este componente se encarga de insertar datos en la tabla *history*, actualizar los campos determinados en la tabla *groups*, descargar los documentos del grupo indicado por el mensaje que recibe de la cola y almacenarlos en el índice de ElasticSearch *groups*. 

Para la prueba unitaria se ejecuta el archivo de python *downloader_PruebaUnitaria.py* que se encuentra en:
> pruebas/pruebaUnitaria_downloader/downloader_PruebaUnitaria.py

Este archivo publica cuatro mensajes a la cola que el downloader revisa con el formato

```json
{
    "id_job": "{INT}", 
    "grp_number": "{INT}"
}
```
Todos los mensajes poseen un id_job de 0 y el grp_number va desde el 0 hasta el número 3.

Además, para fines de la prueba se agregaron los records necesarios a las tablas *jobs* y *groups* desde MySQL Workbench.

<div style="text-align: center;"><img src=https://i.imgur.com/UPR4Trx.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/NoXeBmL.jpg></div>


- Primero, cada 2 segundos se publica un mensaje, en la siguiente foto se puede observar que todos los mensajes han sido publicados. En el primer momento en que una de las réplicas del downloader recibe un mensaje inicia con sus tareas. 

<div style="text-align: center;"><img src=https://i.imgur.com/BTk86xY.jpg></div>


- En los *logs* de cada replica del componente Downloader, que se pueden visualizar desde el programa *lens*, se pueden apreciar las notificaciones que demuestran que las funciones se están ejecutando existosamente.

<div style="text-align: center;"><img src=https://i.imgur.com/VcH0rlm.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/bIsD6sl.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/Nd0DWeX.jpg></div>


- Desde MySQL Workbench se puede consultar las tablas para verificar si los records se han añadido a la tabla *history* y si los campos de la tabla *groups* se han actualizado correctamente. 
- Los campos *status*, *end* y *message* de la tabla *history* se han actualizado, al igual que el *status* del grupo en la tabla *groups*. 

History
<div style="text-align: center;"><img src=https://i.imgur.com/XVti4iW.jpg></div>

Groups
<div style="text-align: center;"><img src=https://i.imgur.com/BMD5mJt.jpg></div>


- Desde RabbitMQ se puede observar que los cuatro mensajes por parte del Downloader han sido publicados, listos para ser consumidos por el siguiente componente.

<div style="text-align: center;"><img src=https://i.imgur.com/eYzdARv.jpg></div>


- Por último, desde ElasticSearch se puede comprobar que los mensajes han sido almacenados existosamente en el índice correspondiente. En la primera imagen se puede ver el texto resaltado, que indica que se encontraron 4 elementos en el índice. En las siguientes imágenes se puede observar que lo que se publicó a ElasticSearch posee el formato establecido por el grupo al igual que el campo de docs con los 10 documentos del grupo. 

<div style="text-align: center;"><img src=https://i.imgur.com/6maFZVS.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/2HUp5qf.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/SShYxFv.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/3E2ScR1.jpg></div>

<div style="text-align: center;"><img src=https://i.imgur.com/D4k1XNT.jpg></div>

### Pruebas Unitarias de **Details Downloader**
El Details Downloader se va a encargar de tomar el rel_doi de cada documento de elasticsearch para buscar los detalles por medio del api si es que estos existen. Por último, le va a agregar los detalles al documento.
Ubicación del script de prueba: \Images\Details Downloader\UnitTest\test.json
Ubicación del JSON de prueba: \Images\Details Downloader\UnitTest\prueba.json

Así es como se ve uno de los documentos de prueba antes de ser procesado

<div style="text-align: center;"><img src=https://user-images.githubusercontent.com/60998008/203886364-78017e5c-8906-4c94-8db1-ed39ac8a63ea.png></div>

Luego cambiamos los valores de: ELASTICPASS, MARIADBPASS, y RABBITPASS por los que corresponden a los passwords generados para los deployments actuales y corremos el script de prueba.
Cuando revisamos el índice, podemos ver que se ha agregado el field details.

<div style="text-align: center;"><img src=https://user-images.githubusercontent.com/60998008/203886406-338eae8c-a2ac-4251-9b0a-201ea6d67303.png></div>

En MariaDB podemos ver que la tabla history tiene la entrada completada

<div style="text-align: center;"><img src=https://user-images.githubusercontent.com/60998008/203886426-7eceeede-1dcc-4cde-8266-81d2e47401ee.png></div>

También podemos ver el cambio en la tabla groups

<div style="text-align: center;"><img src=https://user-images.githubusercontent.com/60998008/203886459-6cdb00d6-369b-45c0-a2b5-827a09104422.png></div>

### Pruebas Unitarias de **Jatsxml Processor**
Para ejecutar la prueba unitaria del Jatsxml Processor se necesita de dos cosas:
* Instalar las bases de datos y RabbitMQ
* Instalar el componente
* Cambiar las credenciales del script de prueba
* Ejecutar el script de prueba

Las credenciales del script se cambian como dice en la seccion de [contraseña](#contraseñas). El script de prueba se encuentra en la carpeta: *Images->Jatsxml Processor->UnitTest->[test.py]()*

Para la prueba se procesara un "group" previamente creado con 5 documentos donde cada uno tiene el partado jatsxml en details, este "group" se encuentra en: *Images->Jatsxml Processor->UnitTest->[prueba.json]()*

Al ejecutar la prueba la cola de donde consume el componente se le manda el siguiente mensaje:

```json
{
    "id_job": "1",
    "grp_number": "3"
}
```

<div style="text-align: center;"><img src=https://i.imgur.com/g3CO0kw.png></div>

Se crea un group y un job en mariaDB:
<div style="text-align: center;"><img src=https://i.imgur.com/gbbVkC0.png></div>

<div style="text-align: center;"><img src=https://i.imgur.com/KTOrXpI.png></div>

El group [prueba.json]() se introduce en elasticsearch en el indice groups:
<div style="text-align: center;"><img src=https://i.imgur.com/Zkp8ETo.png></div>

#### Resultados:
Los logs que se reflejan en el componente son los siguientes:
<div style="text-align: center;"><img src=https://i.imgur.com/9jKlFvm.png></div>

En elasticsearch, el indice "registries" que es el nombre puesto en el values.yaml del App se publican 5 documentos:
<div style="text-align: center;"><img src=https://i.imgur.com/pm4tsyk.png></div>

Los documentos tienen jatsxml:
<div style="text-align: center;"><img src=https://i.imgur.com/af1gQMl.png></div>

El jobs se actualiza:
<div style="text-align: center;"><img src=https://i.imgur.com/Byxz558.png></div>

La tabla history se actualiza:
<div style="text-align: center;"><img src=https://i.imgur.com/mJu9IPt.png></div>

La tabla groups se actualiza:
<div style="text-align: center;"><img src=https://i.imgur.com/jOTP7a1.png></div>



### Prueba unitaria del API

Para ejecutar estas pruebas se necesitan "unitTest.py" y "script.py" localizadas en el branch del Api, además tener en cuenta que se trabajarán de manera local y controlada.

Para iniciar se debe ejecutar el archivo script.py y darle a la opción "4"  
* Crea una database en MariaDB, la cual se llamará "pruebaUnitaria"
* Crea un indice llamado "articulos" y hace un mapping a un field en específico, para que no existan problemas a la hora de realizar el search en Elastic.
* Por último, inserta 200 artículos en el indice creado anteriormente.

Antes de ejecutar todas las pruebas se debe actualizar todas las credenciales de las bases de datos.
![](https://i.imgur.com/mgJZmNf.png)

El archivo "unitTest.py" está conformado por 12 funciones, cada una dividida de tal forma que se pueda mostrar los casos en donde la ejecución es exitosa como no, ambas se diferencian al final del nombre con un OK o un FAIL.
![](https://i.imgur.com/kE3zRo2.png)

1. **Test insertar un job:** Lo que hace es insertar un job en MariaDB, especificamente en la base de datos creada en el script, la primera prueba se hace de manera correcta en donde la petición envía un número para dividir los grupos. En la segunda opción, se envía la petición vacía la cual provoca un error en la inserción.
2. **Test buscar articulos:** Hace un search en Elastic, en donde su query es la petición indicada al inicio de cada función. Para la primera prueba, se manda una petición que devuelve una respuesta este caso se toma como un OK, en el segundo caso se manda una palabra desconocida lo que provoca que no devuelva ningún artículo, este caso se toma como un FAIL.
3. **Test detalles de un articulo:** Busca el match con el título del artículo seleccionado y despliega la información. En el caso OK se toma un titulo existente el cual devolvió el search de elastic, para el caso FAIL se toma un título inexistente en la lista devuelta por Elastic. 
4. **Test like:** Lo que hace es guardar en firebase el artículo al cual se le dio like. En el caso correcto, se selecciona un artículo que anteriormente no estaba guardado en la lista de likes en firebase, el caso FAIL se toma un articulo que anteriormente ya estaba guardado por lo que se toma como un error a la hora de guardarlo.
5. **Test lista de likes:** Despliega la lista del artículos guardados en firebase, según uid del usuario. Se toma como OK cuando se despliega una lista de artículos y el uid del usurio es correcto. El caso FAIL se toma cuando el uid no tiene una lista de likes y no se despliega nada.
6. **Test detalles like:** Despliega la información del artículo guardado en firebase, en la lista de likes del usuario. Se toma como OK cuando el título hace match y se abre la información del artículo. El caso FAIL sería ctulo indicado no hace match.  

Resultado de la prueba:  
![](https://i.imgur.com/bucx8XH.png)


## Recomendaciones.
1. Si se utiliza el navegador de internet Chrome o Microsoft Edge, se recomienda instalar la extensión [JSON Formatter](https://chrome.google.com/webstore/detail/json-formatter/bcjindcccaagfpapjjmafapmmgkkhgoa) para poder visualizar el API de BioRxiv formateado de forma que se tiene más legibilidad y mejor navegabilidad para leer el JSON.

2. Se recomienda mantener las variables con las credenciales locales utilizadas para conectarse a ElasticSearch, MariaDB y RabbitMQ en el código fuente de los componentes, de forma comentada, con el fin de tener fácil acceso a ellas en caso de que sea necesario realizar pruebas locales. 

3. Buen conocimiento con transacciones dentro de bases de datos SQL para el uso de varias replicas y buena concurrencia. Esto pues al momento de tener varias réplicas del componente de Loader, puede darse la situación donde varios pods tomen el mismo job, procesándolo varias veces.

4. El uso de contadores es algo simple pero funcional para las métricas, dentro de la librería de prometheus_client se pueden encontrar, esto es porque al momento de procesar X tarea, simplemente el contador se aumenta sin tanta complicación.

5. El uso de Summary nos ayuda en gran medida con la medición de tiempos de procesamiento por parte de cualquier componente que lo necesita, pues este nos da un recuento del tiempo que se ha tardado en X proceso y la cantidad de veces que se ha realizado.


6. Cuando se trabaja con Thunkable es importante entender el manejo y creación de las funciones a la hora de programar con bloques, pues facilita mucho tener un orden en el código y ejecutar las funcionalidades de la mejor manera.

7. Al trabajar con ngrok, pueden existir conflictos con solicitudes http y demás. En estos casos, lo ideal es utilizar  el Intercambio de Recursos de Origen Cruzado (CORS) en Python.

8. Se recomienda a nuevos integrantes del proyecto que no conocen el funcionamiento de este, consultar a los miembros del equipo cómo funciona para poder hacer pruebas e integrar sus partes sin problemas.

9. Se recomienda en caso de tener suficientes recursos, remover las limitaciones de recursos establecidas a los deployments. En este caso se usaron porque sin estas no nos corría.

10. Se recomienda crear una estructura inicial en el repositorio antes de iniciar cualquier proyecto, de esta forma las branches que se creen del main, pueden ser juntadas facilmente sin muchos conflictos

## Conclusiones. 
1. La práctica del desarrollo de pipelines de un RestAPI es muy relevante hoy en día porque son utilizados en aplicaciones populares que implementan bases de datos en la nube como *Instagram*, *Telegram* y *Facebook*. Además, existe gran cantidad de páginas web que implementan los RestAPI, por lo que el conocimiento de este tipo de interfaces es de gran valor para los integrantes del equipo con interés en esta área. 

2. Elasticsearch es una base de datos NoSQL que resulta conveniente para el caso de uso del presente proyecto, pues se encuentra optimizado para realizar búsquedas de texto, entonces es más beneficioso sobre otras bases de datos como MongoDB; dado que lo que se busca es realizar búsquedas de artículos científicos, lo que implica realizar búsquedas de texto.

3. El uso de bases de datos SQL es bastante funcional en el caso de tener alta concurrencia y tener control sobre el sobre la consistencia de los datos y saber que cada Job ha sido procesado solo una vez por un componente. A su vez tener un historial de trabajo para tener gran trazabilidad sobre las cosas que han sucedido.

4. Firebase es una base de datos muy simple de utilizar, especialmente cuando se trabaja con Thunkable esto se debe a que  se puede conectar de una manera muy simple y su sistema de autenticación es eficiente.

5. Thunkable es una herramienta sencilla pero también es una plataforma que brinda muchas funcionalidades y robustez. Especialmente al desplegar listas y el manejo de las visibilidades en los elementos del diseño.

6. El uso de réplicas permite acelerar procesos en los que se deben procesar muchos documentos como el que se realiza en este proyecto.

7. Para busquedas en elasticsearch, si solo se va a usar una parte del o los documentos que se estan buscando, es buena idea usar el parametro de "source" y pasar una lista con los datos que se necesitan, de esta forma es mas rapida la consulta.

8. Se puede desactivar los mappings dinamicos de elasticsearch de forma parcial con datos que son muy poco predecibles y no tienen un patron. Esto debido a que elasticsearch intentara asignar un tipo de datos para indexar y si despues el tipo de dato era otro va a causar errores. 

9. Parte de lo dicho anteriormente se puede evitar colocando en mappings la opcion llamada 'ignore_malformed' en True, lo que hara que se salte la indexacion de espacios que no sigan cierto patron (solo sirve con ciertos tipos de datos)

10. Siempre es bueno verificar incompatibilidades entre librerias. En este caso, Flask con la opcion de "debug" en true, no permite crear el servidor de metricas de prometheus.


## Anexo 1: Referencias de Internet
Como es bien sabido, no somos conocedores de todas las soluciones ante todos los problemas, es por eso por lo que internet es una gran ayuda ante momentos donde necesitamos de algún tipo de apoyo en alguna sección de nuestro código.
En este apartado veremos las secciones de este proyecto dónde se ha utilizado código fuera de nuestra creación, el funcionamiento y la razón de por qué han sido tomados.
### Clase bcolors
Clase que modifica el color de la letra al momento de las impresiones en pantalla.
#### Código en el Programa
![](https://i.imgur.com/DAlLN6e.png)

#### Funcionamiento
Esta clase nos ayuda para que al momento de realizar impresiones dentro del programa, esto se logra escribiendo el color que necesitamos mostrar y el mensaje que se mostrara, después de haber realizado esto se debe reiniciar el color, esto ya que si no se hace todas las demás impresiones seguirán del mismo color seleccionado.
La clase original solamente contenía los color correspondidos a *[OK,WARNING,FAIL,RESET]*, sin embargo al momento de las pruebas unitarias se notó que hacían falta más colores, es por eso que la clase original ha sido modificada para tener mayor cantidad de opciones.

Un ejemplo práctico de su uso es:
```python!
print(f"{bcolors.OK} REGEX PROCESSOR: {bcolors.RESET} Process Finished")
```
#### Razón de Uso

La razón de su elección es para una mejor legibilidad de mensajes tipo logs que se verán sobre el pod en el momento que la aplicación se encuentre funcionando, pues ver texto plano es más difícil de leer, así que usar esta clase nos hace mas sencillo el proceso de lectura por parte del usuario para saber que esta haciendo el pod en cada momento.



## Referencias bibliográficas

DelftStack. (17 de diciembre del 2020). *Texto de color impreso en Python*. Delft Stack. https://www.delftstack.com/es/howto/python/python-print-colored-text/

GeeksforGeeks. (27 de junio del 2022). *Print Colors in Python terminal*. https://www.geeksforgeeks.org/print-colors-python-terminal/ 