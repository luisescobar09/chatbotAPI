import requests, json, web, pyrebase
from fpdf import FPDF
from os import remove, path
import firebase_admin
from firebase_admin import storage as admin_storage, credentials

urls = ('/data', 'GetData',
		'/delete', 'DeleteData',
		'/delete_unread', 'DeleteUnread')

firebaseConfig = {
					'apiKey': "AIzaSyAV5GQLmw2S_yA_2hTYvd2-0v25pO-aQwM",
					'authDomain': "chatbot-af6db.firebaseapp.com",
					'databaseURL': "https://chatbot-af6db-default-rtdb.firebaseio.com",
					'storageBucket': "chatbot-af6db.appspot.com",
				}

class GetData(object):
	
	def POST(self):
		try:
			form = web.input()			
			fecha = form['fecha']
			conversacion = json.loads(form['conversacion'])
			title = 'Conversación'+' fecha: '+fecha
			pdf = FPDF('P', 'mm', 'Letter') # Create a PDF object
			title = 'Conversación'+' fecha: '+fecha

			pdf.alias_nb_pages() # get total page numbers
			pdf.set_auto_page_break(auto = True, margin = 15) # Set auto page break
			pdf.add_page()
			pdf.image('./static/logo.png', 12, 5, 25)
			pdf.set_font('helvetica', 'B', 18) # font
			title_w = pdf.get_string_width(title) + 6 # Calculate width of title and position
			doc_w = pdf.w
			pdf.set_x((doc_w - title_w) / 2)
			# colors of frame, background, and text
			pdf.set_draw_color(220, 50, 50) # border = red
			pdf.set_text_color(0, 80, 180) # text = blue
			pdf.set_line_width(1.5) # Thickness of frame (border)
			pdf.cell(title_w, 15, title, border=1, ln=1, align='C') # Title
			pdf.ln(20) # Line break

			pdf.set_y(50)
			pdf.set_font('helvetica', 'B', 10)
			contador = 0
			pdf.set_draw_color(255, 255, 255) # border = red
			for i in conversacion:
					pdf.set_text_color(0, 0, 0)
					pdf.ln(1)
					if i == conversacion[contador-1]:
							pass
					else:
							if i.count('User:') > 0:
									pdf.set_x(15)
									pdf.set_fill_color(145, 222, 159)
									pdf.cell(pdf.get_string_width(i) + 10, 10, i, 1, align='L', fill=True)
							else:
									pdf.set_x(85)
									title_w = pdf.get_string_width(i)
									pdf.set_fill_color(136, 173, 245)
									pdf.set_fill_color(136, 173, 245)
									if len(i) > 80:
											pdf.multi_cell(115, 5, i.replace('nuestro [sitio web]','').replace('(','').replace(')',''), 1, align='J', fill=True)
											pdf.ln(1)
									else:
											pdf.multi_cell(title_w + 6, 10, i.replace('nuestro [sitio web]','').replace('(','').replace(')',''), 1, align='R', fill=True)
					contador+=1
			pdf.set_y(254)  # Set position of the footer
			pdf.set_font('Times', 'I', 9.5) # set font
			pdf.set_text_color(169,169,169) # Set font color grey
			pdf.cell(0, 10, f'Página {pdf.page_no()}', align='C') # Page number
			filename = './static/'+fecha+'.pdf'
			pdf.output(filename)

			if path.exists(filename):
				firebase = pyrebase.initialize_app(firebaseConfig)
				storage = firebase.storage()
				storage.child("conversaciones/"+fecha+".pdf").put(filename)
				pdf_url = storage.child("conversaciones/"+fecha+".pdf").get_url()
				if pdf_url is not None: #VALIDA SI EL PDF SI SE GUARDÓ EN BD
					firebase = None
					storage = None
					nombre = form['nombre']
					telefono = form['telefono']
					datos = {
						'fecha': fecha,
						'nombre': nombre,
						'telefono': telefono,
						'conversacion': pdf_url
					}
					response = requests.post('https://chatbot-af6db-default-rtdb.firebaseio.com/no_leidos.json', data = json.dumps(datos)) #ENVÍA LOS DATOS A LA BD
					response = requests.get('https://chatbot-af6db-default-rtdb.firebaseio.com/devices_allowed.json')
					items = response.json()
					encoded = json.dumps(items)
					decoded = json.loads(encoded)
					tokens = []
					for i in decoded:
						tokens.append(decoded[i]['device_token'])
					if response.status_code == 200: #LIBERA LA NOTIFICACIÓN
						remove(filename)
						fcm_api = "AAAA6e8yV-4:APA91bHUeqWm6oYUtSjO1M5BiRWvHpY4Yx5zplgUPK6TgsmNIsC3ldQlX9nnd7JUpxAGAgNjO5yfGW3ow-XaY-droAeVY62H-1FkJSo8iug8lj2VIzh9WB5GJwmh3quR3Kfb6jSrnZXl"
						url = "https://fcm.googleapis.com/fcm/send"
						headers = {
						"Content-Type":"application/json",
						"Authorization": 'key='+fcm_api}
						payload = {
							"registration_ids" : tokens,
							"priority" : "high",
							"notification" : {
								"body" : nombre + ' necesita tu ayuda, contactal@ lo más pronto posible...',
								"link" : "https://chatbotwebapp.josluisluis13.repl.co/",
								"title" : 'Nueva solicitud de contacto',
								"icon": "https://www.pngfind.com/pngs/m/126-1269385_chatbots-builder-pricing-crozdesk-chat-bot-png-transparent.png",
								
							}
						}

						result = requests.post(url,  data=json.dumps(payload), headers=headers )
						result = {}
						result['status'] : 200
						return json.dumps(result)
		except:
			result = {}
			result['status'] : 500
			return json.dumps(result)

class DeleteData(object):
	def POST(self):
		try:
			form = web.input()
			id_request = form['id']
			fecha = form['fecha']
			result = requests.get('https://chatbot-af6db-default-rtdb.firebaseio.com/leidos/'+id_request+'.json')
			items = result.json()
			encoded = json.dumps(items)
			decoded = json.loads(encoded)
			print('Recibió los datos')
			if decoded is not None: #SIGNIFICA QUE SI EXISTE EL ID (ES VÁLIDO)
				if fecha == decoded['fecha']: #COMPRUEBA SI ES LA MISMA FECHA
					print('ES LA MISMA FECHA')
					firebase = pyrebase.initialize_app(firebaseConfig)
					storage = firebase.storage()
					pdf_url = storage.child("conversaciones/"+fecha+".pdf").get_url()
					firebase = None
					storage = None
					if pdf_url == decoded['conversacion']: #COMPRUEBA SI LA URL ES LA MISMA QUE LA QUE ESTÁ EN LA BD
						print('PDF si existe')
						try:
							cred = credentials.Certificate(json.load(open('static/chatbot-af6db-firebase-adminsdk-mw6iz-9db7fcffc1.json')))
							admin_file = firebase_admin.initialize_app(cred, {'storageBucket': "chatbot-af6db.appspot.com"} )
							bucket = admin_storage.bucket()
							blob = bucket.blob('conversaciones/'+fecha+'.pdf')
							blob.delete()
							result = requests.delete('https://chatbot-af6db-default-rtdb.firebaseio.com/leidos/'+id_request+'.json')
							admin_file = None
							bucket = None
						except Exception as e:
							print(e)

		except Exception as e:
			print(e)

if __name__ == "__main__":
   app = web.application(urls, globals()) 
   app.run()