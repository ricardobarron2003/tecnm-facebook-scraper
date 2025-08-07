from flask import Flask, request, jsonify
from chatbot import obtener_respuesta_chatbot  # Importa tu función de chatbot

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    mensaje = data.get('mensaje', '')
    
    # Aquí integras tu lógica de chatbot
    respuesta = obtener_respuesta_chatbot(mensaje)
    
    return jsonify({
        'respuesta': respuesta,
        'status': 'success'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))