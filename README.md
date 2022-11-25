# Journal-Search-Platform-JSP
Prueba unitaria del Details Downloader

El Details Downloader se va a encargar de tomar el rel_doi de cada documento de elasticsearch para buscar los detalles por medio del api si es que estos existen. Por último, le va a agregar los detalles al documento.
Ubicación del script de prueba: \Images\Details Downloader\UnitTest\test.json
Ubicación del JSON de prueba: \Images\Details Downloader\UnitTest\prueba.json

Así es como se ve uno de los documentos de prueba antes de ser procesado
![image](https://user-images.githubusercontent.com/60998008/203886364-78017e5c-8906-4c94-8db1-ed39ac8a63ea.png)
Luego cambiamos los valores de: ELASTICPASS, MARIADBPASS, y RABBITPASS por los que corresponden a los passwords generados para los deployments actuales y corremos el script de prueba.
Cuando revisamos el índice, podemos ver que se ha agregado el field details.
![image](https://user-images.githubusercontent.com/60998008/203886406-338eae8c-a2ac-4251-9b0a-201ea6d67303.png)
En MariaDB podemos ver que la tabla history tiene la entrada completada
![image](https://user-images.githubusercontent.com/60998008/203886426-7eceeede-1dcc-4cde-8266-81d2e47401ee.png)
También podemos ver el cambio en la tabla groups
![image](https://user-images.githubusercontent.com/60998008/203886459-6cdb00d6-369b-45c0-a2b5-827a09104422.png)
Recomendaciones

- Se recomienda a nuevos integrantes del proyecto que no conocen el funcionamiento de este, consultar a los miembros del equipo cómo funciona para poder hacer pruebas e integrar sus partes sin problemas.

- Se recomienda en caso de tener suficientes recursos, remover las limitaciones de recursos establecidas a los deployments. En este caso se usaron porque sin estas no nos corría.

Conclusiones
-El uso de réplicas permite acelerar procesos en los que se deben procesar muchos documentos como el que se realiza en este proyecto
