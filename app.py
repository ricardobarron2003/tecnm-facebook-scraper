from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import os

# Carga mínima inicial
load_dotenv()
app = Flask(__name__)

# HTML incrustado directamente en el código
HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Chatbot TecNM</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f2f2f2;
        }
        #chatbox {
            width: 100%;
            max-width: 600px;
            margin: auto;
            border: 1px solid #ccc;
            padding: 10px;
            background: white;
            height: 400px;
            overflow-y: auto;
        }
        .user {
            text-align: right;
            color: blue;
        }
        .bot {
            text-align: left;
            color: green;
        }
        #inputSection {
            display: flex;
            max-width: 600px;
            margin: 10px auto;
        }
        input[type="text"] {
            flex: 1;
            padding: 10px;
            font-size: 1em;
        }
        button {
            padding: 10px;
            font-size: 1em;
        }
    </style>
</head>
<body>

    <h2 style="text-align: center;">Chatbot TecNM</h2>

    <div id="chatbox"></div>

    <div id="inputSection">
        <input type="text" id="userInput" placeholder="Escribe un mensaje...">
        <button onclick="sendMessage()">Enviar</button>
    </div>

    <script>
        function appendMessage(text, className) {
            const div = document.createElement('div');
            div.className = className;
            div.textContent = text;
            document.getElementById('chatbox').appendChild(div);
            document.getElementById('chatbox').scrollTop = document.getElementById('chatbox').scrollHeight;
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            appendMessage("Tú: " + message, 'user');
            input.value = '';

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: message })
                });

                const data = await response.json();
                appendMessage("Bot: " + data.response, 'bot');
            } catch (error) {
                appendMessage("Error al contactar con el chatbot.", 'bot');
                console.error(error);
            }
        }

        document.getElementById('userInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>

</body>
</html>
"""

# Ruta raíz con HTML incrustado
@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

# Ruta para chatbot
def get_chatbot():
    from chatbot import ChatbotTecNM
    return ChatbotTecNM()

@app.route('/chat', methods=['POST'])
def chat():
    chatbot = get_chatbot()
    data = request.json
    response = chatbot.generate_response(data.get('query', ''))
    return jsonify({"response": response})

# Ejecución
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
