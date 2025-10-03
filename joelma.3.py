import speech_recognition as sr
from gtts import gTTS
from playsound import playsound
import datetime
import os
import time
import ast, operator, re
import math
import tempfile

# Tente importar o pyttsx3 para a função de fala offline (opcional)
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


# Setup
os.makedirs('data', exist_ok=True)
AGENDA_FILE = os.path.join('data','agenda.txt')
if not os.path.exists(AGENDA_FILE):
    open(AGENDA_FILE,'w', encoding='utf-8').close()

# --- INICIALIZAÇÃO OTIMIZADA ---
r = sr.Recognizer()
# Calibra o microfone UMA VEZ no início para economizar tempo
with sr.Microphone() as source:
    print("Calibrando o microfone para o ruído ambiente, por favor aguarde...")
    r.adjust_for_ambient_noise(source, duration=1.5)
    print("Microfone calibrado.")

# --- FUNÇÕES DE FALA ---

# Função de fala original (online, mais lenta) que será usada pelo código
def speak(text):
    print("[SPEAK ONLINE]", text)
    tts = gTTS(text=text, lang='pt')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        filename = fp.name
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# Função de fala alternativa (offline, muito mais rápida)
def speak_offline(text):
    if not PYTTSX3_AVAILABLE:
        print("Biblioteca pyttsx3 não encontrada. Usando gTTS online.")
        speak(text)
        return
    print("[SPEAK OFFLINE]", text)
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "brazil" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()


# --- FUNÇÃO DE ESCUTA OTIMIZADA ---
def listen(timeout=5, phrase_time_limit=6):
    with sr.Microphone() as source:
        try:
            print("Ouvindo...")
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            print("Reconhecendo...")
            recognized_text = r.recognize_google(audio, language='pt-BR').lower()
            return recognized_text
        except sr.WaitTimeoutError:
            print("Timeout: Nenhum áudio detectado.")
            return ""
        except sr.UnknownValueError:
            print("Não foi possível entender o áudio.")
            return ""
        except sr.RequestError as e:
            print(f"Erro no serviço de reconhecimento; {e}")
            return ""
        except Exception as e:
            print(f"Erro na escuta: {e}")
            return ""

# Funções de agenda (sem alterações)
def add_event(text):
    data_cadastro = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    with open(AGENDA_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{data_cadastro}] Evento: {text}\n")
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

# Funções de matemática (sem alterações)
def safe_eval(expr):
    expr = expr.lower()
    expr = re.sub(r'\b(x|vezes)\b', '*', expr)
    expr = re.sub(r'\b(mais)\b', '+', expr)
    expr = re.sub(r'\b(menos)\b', '-', expr)
    expr = re.sub(r'\b(dividido por|dividido|por)\b', '/', expr)
    expr = expr.replace(',', '.')
    expr = re.sub(r'[^0-9+\-*/().^sqrt ]','',expr)
    expr = expr.replace("^", "**")
    if "sqrt" in expr:
        try:
            num = float(expr.replace("sqrt", "").strip("() "))
            return math.sqrt(num)
        except: raise ValueError("Expressão de raiz inválida")
    if not any(c in expr for c in "+-*/"): # Se for só um número, não calcule
        raise ValueError("Expressão incompleta")
    node = ast.parse(expr, mode='eval')
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
    def _eval(n):
        if isinstance(n, ast.Expression): return _eval(n.body)
        if isinstance(n, ast.BinOp):
            l, r = _eval(n.left), _eval(n.right)
            return ops[type(n.op)](l,r)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub): return -_eval(n.operand)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
        raise ValueError("Expressão inválida")
    return _eval(node)


### ADICIONADO ### - Início da função de equações completa
def resolver_equacao(text):
    def get_coefficient(name):
        """Pede e ouve um coeficiente numérico."""
        speak(f"Qual o valor de {name}?")
        while True:
            try:
                # Usa um tempo maior para ouvir a resposta do coeficiente
                coeff_str = listen(timeout=6, phrase_time_limit=5)
                if coeff_str:
                    return float(coeff_str)
                else:
                    speak("Não ouvi o número, por favor, repita.")
            except (ValueError, TypeError):
                speak("Não entendi. Por favor, diga apenas o número.")

    if "primeiro grau" in text:
        speak("Entendido. Para a equação de primeiro grau, preciso dos coeficientes A e B.")
        a = get_coefficient("A")
        b = get_coefficient("B")
        if a == 0:
            speak("O coeficiente 'a' não pode ser zero em uma equação de primeiro grau.")
            return
        x = -b / a
        speak(f"A raiz da equação é x = {x:.2f}")

    elif "segundo grau" in text:
        speak("Entendido. Para a equação de segundo grau, preciso dos coeficientes A, B e C.")
        a = get_coefficient("A")
        b = get_coefficient("B")
        c = get_coefficient("C")
        if a == 0:
            speak("O coeficiente 'a' não pode ser zero em uma equação de segundo grau.")
            return
        
        delta = (b**2) - (4*a*c)
        
        if delta < 0:
            speak(f"A equação não possui raízes reais, pois o delta é negativo, valendo {delta:.2f}.")
        elif delta == 0:
            x = -b / (2*a)
            speak(f"A equação possui uma raiz real: x = {x:.2f}")
        else:
            x1 = (-b + math.sqrt(delta)) / (2*a)
            x2 = (-b - math.sqrt(delta)) / (2*a)
            speak(f"A equação possui duas raízes reais. X1 é igual a {x1:.2f}, e X2 é igual a {x2:.2f}")
    else:
        speak("Não entendi o tipo de equação. Diga 'resolver equação de primeiro grau' ou 'segundo grau'.")
### ADICIONADO ### - Fim da função de equações completa


# --- LOOP PRINCIPAL MELHORADO ---
speak("Assistente pronta. Diga 'Ok sexta-feira' para ativar.")

try:
    while True:
        print("\nAguardando wake word...")
        wake = listen(timeout=10, phrase_time_limit=4)
        if any(w in wake for w in ["ok sexta-feira","ok sexta feira","sexta-feira","sexta feira"]):
            speak("Sim?")
            cmd = listen(timeout=6, phrase_time_limit=7)
            print("Comando:", cmd)
            if not cmd:
                speak("Não ouvi nenhum comando.")
                continue

            # CADASTRAR EVENTO
            if any(w in cmd for w in ["cadastrar evento", "novo evento", "adicionar evento"]):
                speak("Ok, qual evento devo cadastrar?")
                ev = listen(timeout=8, phrase_time_limit=10)
                if ev: add_event(ev)
                else: speak("Não consegui ouvir o evento.")

            # LER AGENDA
            elif any(w in cmd for w in ["ler agenda", "mostrar agenda", "ver agenda"]):
                read_agenda()

            # LIMPAR AGENDA
            elif any(w in cmd for w in ["limpar agenda", "apagar agenda"]):
                clear_agenda()

            # HORAS
            elif any(w in cmd for w in ["que horas", "horas são", "hora"]):
                now = datetime.datetime.now().strftime("%H:%M")
                speak(f"Agora são {now}.")

            # DATA
            elif any(w in cmd for w in ["que dia", "dia de hoje", "data"]):
                today = datetime.datetime.now().strftime("%d de %B de %Y")
                speak(f"Hoje é {today}.")

            ### ADICIONADO ### - Comando para chamar a função de equações
            elif any(w in cmd for w in ["equação", "resolver"]):
                resolver_equacao(cmd)

            # SAIR
            elif any(w in cmd for w in ["sair", "encerrar", "desligar"]):
                speak("Encerrando assistente. Até mais.")
                break

            # SE NENHUM COMANDO ACIMA, TENTE CALCULAR
            else:
                try:
                    res = safe_eval(cmd)
                    speak(f"O resultado é {res}")
                except (ValueError, SyntaxError):
                    speak("Comando não reconhecido. Tente novamente.")

except KeyboardInterrupt:
    speak("Encerrando por interrupção.")
except Exception as e:
    print("Erro principal:", e)
    speak("Ocorreu um erro, veja o console.")