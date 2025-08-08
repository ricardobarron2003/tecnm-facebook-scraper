from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

# Carga mínima inicial
load_dotenv()
app = Flask(__name__)

# Carga diferida del chatbot solo cuando sea necesario
def get_chatbot():
    from chatbot import ChatbotTecNM
    return ChatbotTecNM()

@app.route('/chat', methods=['POST'])
def chat():
    chatbot = get_chatbot()  # Se carga solo al recibir peticiones
    data = request.json
    response = chatbot.generate_response(data.get('query', ''))
    return jsonify({"response": response})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)