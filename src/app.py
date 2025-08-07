from flask import Flask, request, jsonify
from chatbot import ChatbotTecNM
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
chatbot = ChatbotTecNM()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '')
    response = chatbot.generate_response(query)
    return jsonify({"response": response})

@app.route('/update', methods=['POST'])
def update_publications():
    success = chatbot.run_scraping()
    return jsonify({"success": success, "message": "Publicaciones actualizadas" if success else "Error al actualizar"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))