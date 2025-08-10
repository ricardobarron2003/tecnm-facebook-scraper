from flask import Flask, request, jsonify, render_template_string
import os
import logging

app = Flask(__name__)

# Configura logging para diagnóstico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        .disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        #timer {
            text-align: center;
            margin-top: 5px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>

    <h2 style="text-align: center;">Chatbot TecNM</h2>

    <div id="chatbox"></div>

    <div id="inputSection">
        <input type="text" id="userInput" placeholder="Escribe un mensaje...">
        <button id="sendButton" onclick="sendMessage()">Enviar</button>
    </div>
    <div id="timer"></div>

    <script>
        let isWaiting = false;
        let countdown = 0;
        const WAIT_TIME = 20; // 20 segundos de espera

        function appendMessage(text, className) {
            const div = document.createElement('div');
            div.className = className;
            div.textContent = text;
            document.getElementById('chatbox').appendChild(div);
            document.getElementById('chatbox').scrollTop = document.getElementById('chatbox').scrollHeight;
        }

        function disableInput() {
            const input = document.getElementById('userInput');
            const button = document.getElementById('sendButton');
            input.disabled = true;
            button.disabled = true;
            input.classList.add('disabled');
            button.classList.add('disabled');
            isWaiting = true;
            
            // Iniciar cuenta regresiva
            countdown = WAIT_TIME;
            updateTimer();
            const interval = setInterval(() => {
                countdown--;
                updateTimer();
                if (countdown <= 0) {
                    clearInterval(interval);
                    enableInput();
                }
            }, 1000);
        }

        function enableInput() {
            const input = document.getElementById('userInput');
            const button = document.getElementById('sendButton');
            input.disabled = false;
            button.disabled = false;
            input.classList.remove('disabled');
            button.classList.remove('disabled');
            document.getElementById('timer').textContent = '';
            isWaiting = false;
        }

        function updateTimer() {
            document.getElementById('timer').textContent = 
                `Por favor espera ${countdown} segundos antes de enviar otra consulta`;
        }

        async function sendMessage() {
            if (isWaiting) return;
            
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            appendMessage("Tú: " + message, 'user');
            input.value = '';
            disableInput();

            try {
                appendMessage("Bot: Pensando...", 'bot');
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: message })
                });

                const data = await response.json();
                // Reemplazar el mensaje "Pensando..." con la respuesta real
                const chatbox = document.getElementById('chatbox');
                chatbox.removeChild(chatbox.lastChild);
                appendMessage("Bot: " + data.response, 'bot');
            } catch (error) {
                appendMessage("Bot: Error al contactar con el chatbot.", 'bot');
                console.error(error);
                enableInput(); // Habilitar de nuevo si hay error
            }
        }

        document.getElementById('userInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !isWaiting) {
                sendMessage();
            }
        });
    </script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

# Carga el chatbot una vez al iniciar (singleton)
chatbot = None

def get_chatbot():
    global chatbot
    if chatbot is None:
        from chatbot import ChatbotTecNM
        chatbot = ChatbotTecNM()
    return chatbot

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Formato inválido"}), 400
            
        bot = get_chatbot()
        response = bot.generate_response(data['query'])
        return jsonify({"response": response})
        
    except Exception as e:
        logger.error(f"Error en /chat: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)