# assistant_from_professor_gtts.py
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import datetime
import os
import time
import ast, operator, re

# setup
os.makedirs('data', exist_ok=True)
AGENDA_FILE = os.path.join('data','agenda.txt')
if not os.path.exists(AGENDA_FILE):
    open(AGENDA_FILE,'w', encoding='utf-8').close()

# Inicialização do recognizer
r = sr.Recognizer()

# Função de fala usando gTTS
def speak(text):
    print("[SPEAK]", text)
    tts = gTTS(text=text, lang='pt')
    tts.save("temp.mp3")
    playsound("temp.mp3")
    os.remove("temp.mp3")

# Função de escuta
def listen(timeout=None, phrase_time_limit=5):
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except Exception as e:
            print("listen error:", e)
            return ""
    try:
        return r.recognize_google(audio, language='pt-BR').lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print("recognizer error:", e)
        return ""

# Funções de agenda
def add_event(text):
    with open(AGENDA_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now().isoformat()} - {text}\n")
    speak("Evento cadastrado.")

def read_agenda():
    with open(AGENDA_FILE, 'r', encoding='utf-8') as f:
        lines = [l.strip() for l in f if l.strip()]
    if not lines:
        speak("Sua agenda está vazia.")
        return
    speak(f"Você tem {len(lines)} eventos na agenda.")
    for ln in lines:
        print(ln)
        speak(ln)
        time.sleep(0.3)

def clear_agenda():
    open(AGENDA_FILE, 'w', encoding='utf-8').close()
    speak("Agenda limpa.")

# Avaliação segura de expressões matemáticas
def safe_eval(expr):
    expr = expr.lower()
    expr = re.sub(r'\b(x|vezes)\b', '*', expr)
    expr = re.sub(r'\b(mais)\b', '+', expr)
    expr = re.sub(r'\b(menos)\b', '-', expr)
    expr = re.sub(r'\b(dividido por|dividido|por)\b', '/', expr)
    expr = expr.replace(',', '.')
    expr = re.sub(r'[^0-9+\-*/(). ]','',expr)
    
    node = ast.parse(expr, mode='eval')
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
    
    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.BinOp):
            l = _eval(n.left)
            r = _eval(n.right)
            op = type(n.op)
            if op in ops:
                return ops[op](l,r)
            raise ValueError("Operador não permitido")
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -_eval(n.operand)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        raise ValueError("Expressão inválida")
    
    return _eval(node)

# Loop principal
speak("Assistente pronta. Diga 'Ok sexta-feira' para ativar.")

try:
    while True:
        print("Aguardando wake word...")
        wake = listen(timeout=6, phrase_time_limit=4)
        if any(w in wake for w in ["ok sexta-feira","ok sexta feira","sexta-feira","sexta feira"]):
            speak("Sim, Lord faarquard.")
            cmd = listen(timeout=6, phrase_time_limit=7)
            print("Comando:", cmd)
            if not cmd:
                speak("Não ouvi nenhum comando.")
                continue

            if "cadastrar" in cmd and "evento" in cmd:
                speak("Ok, qual evento devo cadastrar?")
                ev = listen(timeout=8, phrase_time_limit=8)
                if ev:
                    add_event(ev)
                else:
                    speak("Não consegui ouvir o evento.")
            elif "ler" in cmd and "agenda" in cmd:
                read_agenda()
            elif "limpar" in cmd and "agenda" in cmd:
                clear_agenda()
            elif "que horas" in cmd or "horas são" in cmd:
                now = datetime.datetime.now().strftime("%H:%M")
                speak(f"Agora são {now}.")
            elif "que dia" in cmd or "dia é hoje" in cmd:
                today = datetime.datetime.now().strftime("%d de %B de %Y")
                speak(f"Hoje é {today}.")
            elif "calcular" in cmd:
                expr = cmd.replace("calcular", "", 1).strip()
                if not expr:
                    speak("Diga a conta que eu calculo.")
                    expr = listen(timeout=6, phrase_time_limit=6)
                if expr:
                    try:
                        res = safe_eval(expr)
                        speak(f"O resultado é {res}")
                    except Exception as e:
                        print("Erro ao calcular:", e)
                        speak("Desculpe, não consegui calcular essa expressão.")
                else:
                    speak("Não recebi a expressão.")
            elif "sair" in cmd or "encerrar" in cmd:
                speak("Encerrando assistente. Até mais.")
                break
            else:
                speak("Comando não reconhecido. Tente novamente.")

except KeyboardInterrupt:
    speak("Encerrando por interrupção.")
except Exception as e:
    print("Erro principal:", e)
    speak("Ocorreu um erro, veja o console.")
