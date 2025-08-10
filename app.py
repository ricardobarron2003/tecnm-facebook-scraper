from flask import Flask, request, jsonify, render_template_string
import os
import logging
import time

app = Flask(__name__)

# Configura logging para diagnóstico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Pregúntale a TecBot</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1b396a;
            color: white;
        }
        
        h2 {
            text-align: center;
            color: white;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        #chatbox {
            width: 100%;
            max-width: 600px;
            margin: 0 auto 20px;
            border: 1px solid #2a4a7a;
            border-radius: 8px;
            padding: 15px;
            background: white;
            height: 400px;
            overflow-y: auto;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .user {
            text-align: right;
            margin: 10px 0;
            padding: 10px 15px;
            background-color: #e3f2fd;
            border-radius: 18px 18px 0 18px;
            color: #0d47a1;
            display: inline-block;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .bot {
            text-align: left;
            margin: 10px 0;
            padding: 10px 15px;
            background-color: #f1f1f1;
            border-radius: 18px 18px 18px 0;
            color: #333;
            display: inline-block;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        #inputSection {
            display: flex;
            max-width: 600px;
            margin: 0 auto;
            gap: 10px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 12px 15px;
            font-size: 1em;
            border: 1px solid #2a4a7a;
            border-radius: 6px;
            background-color: white;
            color: #333;
        }
        
        button {
            padding: 12px 25px;
            font-size: 1em;
            background-color: #2a4a7a;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: background-color 0.3s;
        }
        
        button:hover {
            background-color: #1c355e;
        }
        
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        
        #timer {
            text-align: center;
            margin-top: 10px;
            color: #a0c4ff;
            font-size: 0.9em;
        }
    </style>
</head>
<body>

    <h2>Pregúntale a TecBot</h2>

    <div id="chatbox"></div>

    <div id="inputSection">
        <input type="text" id="userInput" placeholder="Escribe un mensaje...">
        <button id="sendButton" onclick="sendMessage()">Enviar</button>
    </div>
    <div id="timer"></div>

    <script>
        let isWaiting = false;
        let countdown = localStorage.getItem('chatbotCountdown') ? parseInt(localStorage.getItem('chatbotCountdown')) : 0;
        const WAIT_TIME = 20; // 20 segundos de espera

        // Verificar si hay un contador activo al cargar la página
        window.onload = function() {
            if (countdown > 0) {
                isWaiting = true;
                disableInput();
                startCountdown();
            }
        };

        function appendMessage(text, className) {
            const div = document.createElement('div');
            div.className = className;
            div.textContent = text;
            document.getElementById('chatbox').appendChild(div);
            document.getElementById('chatbox').scrollTop = document.getElementById('chatbox').scrollHeight;
        }

        function startCountdown() {
            const interval = setInterval(() => {
                countdown--;
                localStorage.setItem('chatbotCountdown', countdown);
                updateTimer();
                
                if (countdown <= 0) {
                    clearInterval(interval);
                    enableInput();
                    localStorage.removeItem('chatbotCountdown');
                }
            }, 1000);
        }

        function disableInput() {
            const input = document.getElementById('userInput');
            const button = document.getElementById('sendButton');
            input.disabled = true;
            button.disabled = true;
            isWaiting = true;
            
            // Guardar el estado en localStorage
            localStorage.setItem('chatbotCountdown', countdown);
            
            // Iniciar cuenta regresiva
            countdown = WAIT_TIME;
            updateTimer();
            startCountdown();
        }

        function enableInput() {
            const input = document.getElementById('userInput');
            const button = document.getElementById('sendButton');
            input.disabled = false;
            button.disabled = false;
            document.getElementById('timer').textContent = '';
            isWaiting = false;
            localStorage.removeItem('chatbotCountdown');
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
                enableInput();
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
chatbot_ready = False

def get_chatbot():
    global chatbot, chatbot_ready
    if chatbot is None:
        try:
            logger.info("Intentando cargar el chatbot...")
            start_time = time.time()
            from chatbot import ChatbotTecNM
            chatbot = ChatbotTecNM()
            load_time = time.time() - start_time
            logger.info(f"Chatbot cargado exitosamente en {load_time:.2f} segundos")
            chatbot_ready = True
        except Exception as e:
            logger.error(f"Error al cargar el chatbot: {str(e)}")
            chatbot_ready = False
    return chatbot if chatbot_ready else None

@app.route('/status')
def status():
    bot = get_chatbot()
    if bot is None:
        return jsonify({"status": "error", "message": "Chatbot no pudo ser cargado"}), 500
    return jsonify({"status": "ok", "message": "Chatbot listo"})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Verificar si el chatbot está listo
        bot = get_chatbot()
        if bot is None:
            logger.error("Chatbot no está disponible")
            return jsonify({"error": "Chatbot no está disponible"}), 503
            
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Formato inválido"}), 400
            
        logger.info(f"Procesando consulta: {data['query']}")
        start_time = time.time()
        response = bot.generate_response(data['query'])
        process_time = time.time() - start_time
        logger.info(f"Consulta procesada en {process_time:.2f} segundos")
        
        return jsonify({"response": response})
        
    except Exception as e:
        logger.error(f"Error en /chat: {str(e)}", exc_info=True)
        return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Precargar el chatbot al iniciar
    get_chatbot()
    app.run(host='0.0.0.0', port=port)