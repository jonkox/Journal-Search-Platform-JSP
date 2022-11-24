import unittest
import uuid
import math
import time



class TestNavegar(unittest.TestCase):

    # Peligros escritos a mano para simular datos de la FireBase
    peligros = {
  "-NFbsys29FiNH5m8J0TD": {
    "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
    "fecha": int(time.time()),
    "latitud": 9.8641821,
    "longitud": -83.9211346,
    "mensaje": "Andrés me grito feo :(",
    "referencias": "Frente al McDonalds",
    "tipo peligro": "Maltrato",
    "ultima modificacion": int(time.time()),
    "votos": 1
  },
  "-NFlq8r7gKXeCoEIuRmf": {
    "comentarios": {
      "-NFmq2BGsBPKmXX25j4t": {
        "mensaje": "Me parece haberlo visto con otra ropa luego",
        "usuario": "deanyt0417@gmail.com"
      }
    },
    "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
    "fecha": 1667283591.17,
    "latitud": 9.8560509,
    "longitud": -83.9116842,
    "mensaje": "Cerca del Fresh Market",
    "referencias": "tipo alto de camisa azul",
    "tipo peligro": "Asalto",
    "ultima modificacion": 1667283591.171,
    "votos": 1
  }
}

    response = ""
    peticion = {"-NFmoOkJ12mJz_eZk2BG": {
                    "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
                    "fecha": 1651535770,
                    "latitud": 9.8591829,
                    "longitud": -83.9106057,
                    "mensaje": "Boe",
                    "referencias": "Si",
                    "tipo peligro": "Asalto",
                    "ultima modificacion": 1651535770,
                    "votos": 13}}


    def test_agregar_peligro_FAIL(self):
        peticion = {
          "-NFbsys29FiNH5m8J0TD": {
            "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
            "fecha": int(time.time()),
            "latitud": 9.8641821,
            "longitud": -83.9211346,
            "mensaje": "Andrés me grito feo :(",
            "referencias": "Frente al McDonalds",
            "tipo peligro": "Maltrato",
            "ultima modificacion": int(time.time()),
            "votos": 1
          }}
        peligroId = "-NFbsys29FiNH5m8J0TD"

        tipo = peticion[peligroId]["tipo peligro"]
        mensaje = peticion[peligroId]["mensaje"]
        ref = peticion[peligroId]["referencias"]
        creador = peticion[peligroId]["creador"]
        if peticion[peligroId]["tipo peligro"] == "" or peticion[peligroId]["mensaje"] == "" or peticion[peligroId]["referencias"] == "":
            response = 'Error: Rellenar todos los espacios'
        elif peticion[peligroId]["creador"] == "":
            response = 'Error: No se pudo obtener el creador'

        # base.child("navegar").child("peligros").order_by_child("latitud").equal_to(peticion["latitud"]).order_by_child("longitud").equal_to(peticion["longitud"]).get().val()) != []
        elif self.peligros[peligroId]["latitud"] == peticion[peligroId]["latitud"] and self.peligros[peligroId]["longitud"] == peticion[peligroId]["longitud"]:
            response = 'Error: Peligro existente en esa ubicacion exacta'
        
        else: 
            response = 'Peligro agregado exitosamente'

        self.assertEqual(response,'Error: Peligro existente en esa ubicacion exacta')
    
    def test_agregar_peligro_OK(self):

        peticion = {
            "-NFbsys29FiNH5m8J0TD": {
                "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
                "fecha": int(time.time()),
                "latitud": 9.86418277,
                "longitud": -83.9215546,
                "mensaje": "Andrés me grito feo :(",
                "referencias": "Frente al McDonalds",
                "tipo peligro": "Maltrato",
                "ultima modificacion": int(time.time()),
                "votos": 1
            }}
        peligroId = "-NFbsys29FiNH5m8J0TD"

        if peticion[peligroId]["tipo peligro"] == "" or peticion[peligroId]["mensaje"] == "" or peticion[peligroId]["referencias"] == "":
            response = 'Error: Rellenar todos los espacios'
        elif peticion[peligroId]["creador"] == "":
            response = 'Error: No se pudo obtener el creador'

        # base.child("navegar").child("peligros").order_by_child("latitud").equal_to(peticion["latitud"]).order_by_child("longitud").equal_to(peticion["longitud"]).get().val()) != []
        elif self.peligros[peligroId]["latitud"] == peticion[peligroId]["latitud"] and self.peligros[peligroId]["longitud"] == peticion[peligroId]["longitud"]:
            response = 'Error: Peligro existente en esa ubicacion exacta',400
        
        else: 
            response = 'Peligro agregado exitosamente'

        self.assertEqual(response,'Peligro agregado exitosamente')

    def test_obtener_peligro_OK(self):
        peligroId = "-NFbsys29FiNH5m8J0TD"

        result = self.peligros["-NFbsys29FiNH5m8J0TD"]
        # return jsonify(base.child("navegar").child("peligros").child(peligroId).get().val()),200
        self.assertEqual(self.peligros["-NFbsys29FiNH5m8J0TD"],result)

    def test_obtener_peligro_FAIL(self):
        peligroId = "-NFmoOkJ12mJz_eZk2BGSS"
        try:
            result = self.peligros["-NFmoOkJ12mJz_eZk2BGSS"]
        except Exception as e:
            result = None
        # return jsonify(base.child("navegar").child("peligros").child(peligroId).get().val()),200
        self.assertEqual(None,result)

    def test_modificar_peligro_OK(self):

        peligroId = "-NFbsys29FiNH5m8J0TD"
        cuerpo = {
                    "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
                    "fecha": 1651535770,
                    "latitud": 9.8591829,
                    "longitud": -83.9106057,
                    "mensaje": "Asaltaron a un muchacho en el TEC",
                    "referencias": "En el lab de Tierra Media",
                    "tipo peligro": "Asalto",
                    "ultima modificacion": 1651555570,
                    "votos": 13}

        if cuerpo["tipo peligro"] == "" or cuerpo["mensaje"] == "" or cuerpo["referencias"] == "":
            self.response = 'Error: Rellenar todos los espacios'
        else:
                
            # base.child("navegar").child("peligros").child(peligroId).child("tipo peligro").set(cuerpo["tipo peligro"])
            # base.child("navegar").child("peligros").child(peligroId).child("mensaje").set(cuerpo["mensaje"])
            # base.child("navegar").child("peligros").child(peligroId).child("referencias").set(cuerpo["referencias"])
            # base.child("navegar").child("peligros").child(peligroId).child("ultima modificacion").set(int(time.time()))
            
            self.peligros[peligroId]["tipo peligro"] = cuerpo["tipo peligro"]
            self.peligros[peligroId]["mensaje"] = cuerpo["mensaje"]
            self.peligros[peligroId]["referencias"] = cuerpo["referencias"]
            self.peligros[peligroId]["ultima modificacion"] = cuerpo["ultima modificacion"]
            self.response = 'Peligro modificado exitosamente'
        
        self.assertEqual(self.response, 'Peligro modificado exitosamente')

    def test_modificar_peligro_FAIL(self):

        peligroId = "-NFmoOkJ12mJz_eZk2BG"
        cuerpo = {
            "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
            "fecha": 1651535770,
            "latitud": 9.8591829,
            "longitud": -83.9106057,
            "mensaje": "",
            "referencias": "En el lab de Tierra Media",
            "tipo peligro": "Asalto",
            "ultima modificacion": 1651555570,
            "votos": 13}

        if cuerpo["tipo peligro"] == "" or cuerpo["mensaje"] == "" or cuerpo["referencias"] == "":
            self.response = 'Error: Rellenar todos los espacios'
        else:

            # base.child("navegar").child("peligros").child(peligroId).child("tipo peligro").set(cuerpo["tipo peligro"])
            # base.child("navegar").child("peligros").child(peligroId).child("mensaje").set(cuerpo["mensaje"])
            # base.child("navegar").child("peligros").child(peligroId).child("referencias").set(cuerpo["referencias"])
            # base.child("navegar").child("peligros").child(peligroId).child("ultima modificacion").set(int(time.time()))

            self.peligros[peligroId]["tipo peligro"] = cuerpo["tipo peligro"]
            self.peligros[peligroId]["mensaje"] = cuerpo["mensaje"]
            self.peligros[peligroId]["referencias"] = cuerpo["referencias"]
            self.peligros[peligroId]["ultima modificacion"] = cuerpo["ultima modificacion"]
            self.response = 'Peligro modificado exitosamente'

        self.assertEqual(self.response, 'Error: Rellenar todos los espacios')

    def test_ver_comentarios_OK(self):
        peticion = {"-NFlq8r7gKXeCoEIuRmf":{
    "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
    "fecha": 1667283591.17,
    "latitud": 9.8560509,
    "longitud": -83.9116842,
    "mensaje": "Cerca del Fresh Market",
    "referencias": "tipo alto de camisa azul",
    "tipo peligro": "Asalto",
    "ultima modificacion": 1667283591.171,
    "votos": 1
  }}

        peligroId = "-NFlq8r7gKXeCoEIuRmf"
        uid = "-NFmq2BGsBPKmXX25j4t"
        latitud = peticion["-NFlq8r7gKXeCoEIuRmf"]["latitud"]
        longitud = peticion["-NFlq8r7gKXeCoEIuRmf"]["longitud"]

        # peligroId = list(
        #     base.child("navegar").child("peligros").order_by_child("latitud").equal_to(latitud).order_by_child(
        #         "longitud").equal_to(longitud).get().val().keys())[0]
        # peligro = base.child("navegar").child("peligros").child(peligroId)

        comentarios = self.peligros[peligroId]["comentarios"][uid]

        listaComentarios = []
        # comentarios = peligro.child("comentarios").get()
        if (comentarios) != None:
            for comentario in comentarios:
                if comentarios["mensaje"] not in listaComentarios:
                    listaComentarios.append(comentarios["mensaje"])
            esCreador = uid
            likes = self.peligros[peligroId]["votos"]

            jsonResponse = {
                "esCreador": esCreador,
                "id": peligroId,
                "comentarios": listaComentarios,
                "likes": likes
            }
        else:
            listaComentarios = False
            jsonResponse = {}
        self.assertNotEqual(jsonResponse,{})

    def test_ver_comentarios_FAIL(self):
        peticion = {"-NFlq8r7gKXeCoEIuRmf": {
            "creador": "vVTZDSAQvia85S8szH2gE4I0ONA3",
            "fecha": 1667283591.17,
            "latitud": 9.8560509,
            "longitud": -83.9116842,
            "mensaje": "Cerca del Fresh Market",
            "referencias": "tipo alto de camisa azul",
            "tipo peligro": "Asalto",
            "ultima modificacion": 1667283591.171,
            "votos": 1
        }}

        peligroId = "-NFlq8r7gKXeCoEIuRmf"
        uid = "-NFmq2BGsBPKmXX25j4t"
        latitud = peticion["-NFlq8r7gKXeCoEIuRmf"]["latitud"]
        longitud = peticion["-NFlq8r7gKXeCoEIuRmf"]["longitud"]

        # peligroId = list(
        #     base.child("navegar").child("peligros").order_by_child("latitud").equal_to(latitud).order_by_child(
        #         "longitud").equal_to(longitud).get().val().keys())[0]
        # peligro = base.child("navegar").child("peligros").child(peligroId)

        comentarios = None

        listaComentarios = []
        # comentarios = peligro.child("comentarios").get()
        if (comentarios) != None:
            for comentario in comentarios:
                if comentarios["mensaje"] not in listaComentarios:
                    listaComentarios.append(comentarios["mensaje"])
            esCreador = uid
            likes = self.peligros[peligroId]["votos"]

            jsonResponse = {
                "esCreador": esCreador,
                "id": peligroId,
                "comentarios": listaComentarios,
                "likes": likes
            }


        else:
            listaComentarios = False
            jsonResponse = {}
        self.assertEqual(jsonResponse, {})

    def test_agregar_comentario_OK(self):
        peticion = {"-NFlq8r7gKXeCoEIuRmf":
                        {
                            "usuario": "correo@gmail.com",
                            "mensaje": "soy un mensaje"
                        }
                    }
        peligrosCopy = self.peligros.copy()

        peligroId = "-NFlq8r7gKXeCoEIuRmf"
        cuerpo = peligrosCopy[peligroId]
        cantidad_antes = len(peligrosCopy[peligroId]['comentarios'])

        # base.child("navegar").child("peligros").child(peligroId).child("comentarios").push(cuerpo)
        # base.child("navegar").child("peligros").child(peligroId).child("ultima modificacion").set(int(time.time()))
        newId = uuid.uuid1()
        peligrosCopy[peligroId]["comentarios"][newId] = cuerpo
        cantidad_despues = len(peligrosCopy[peligroId]['comentarios'])


        self.assertGreater(cantidad_despues,cantidad_antes)

    def test_like_comentario_OK(self):
        peligroId = "-NFbsys29FiNH5m8J0TD"
        votos_antes = self.peligros[peligroId]["votos"]
        self.peligros[peligroId]["votos"] = votos_antes + 1
        votos_despues = self.peligros[peligroId]["votos"]
        self.assertGreater(votos_despues, votos_antes)
        #     base.child("navegar").child("peligros").child(peligroId).child("votos").get().val()
        # base.child("navegar").child("peligros").child(peligroId).child("votos").set(votos_actuales + 1)
        # base.child("navegar").child("peligros").child(peligroId).child("ultima modificacion").set(int(time.time()))
        # return '', 200

    def test_actualizar_marcadores(self):
        peticion = {
            "latitud": 9.8591829,
            "longitud": -83.9106057,
            "ventana" : 10}
        pyreResponsePeligros = self.peligros
        lat1 = peticion["latitud"]
        lon1 = peticion["longitud"]
        ventana = peticion["ventana"]
        listaPeligros = []
        for i in pyreResponsePeligros:
            lat2 = pyreResponsePeligros[i]["latitud"]
            lon2 = pyreResponsePeligros[i]["longitud"]

            if (calcularDistancia(lat1, lon1, lat2, lon2, True)) and (int(time.time()) - pyreResponsePeligros[i]["fecha"] < ventana * 3600):
                listaPeligros.append(pyreResponsePeligros[i])

        self.assertNotEqual(listaPeligros,[])


if __name__ == '__main__':
	unittest.main()