# Web Scraper baseado em python para o projeto de Automação do Senai ITABIRA.
# É utilizado a ferramenta HTML Requests para analisar o site de clima do Google.
# Código original em: https://github.com/S3EMi/Irrigacao-Python-Arduino

from requests_html import HTMLSession
import time
from pyfirmata import Arduino, util, SERVO, STRING_DATA
import os

# Função de pausa bruta
def pause():
    input("\nPressione qualquer tecla para continuar...")

# Função para limpar a janela
def clearConsole():
    os.system('cls')

# Estabelecer o port do Arduino para comunicação e controle.
port = "COM7"
board = Arduino(port)

# Determina os parâmetros iniciais para o scraper
s = HTMLSession()
query = input("Localização: ")

# Transforma o site em HTML e pega as informações necessárias
url = f'https://www.google.com/search?q=weather+{query}'
r = s.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'})
title = r.html.find('span.BBwThe', first=True).text

# No site falava que era bom começar um Iterator pois de acordo com a documentação do Pyfirmata,
# "Para usar portas analógicas, provavelmente é útil iniciar um thread do iterador. 
# Caso contrário a placa continuará enviando dados para sua serial, até que ela transborde"
it = util.Iterator(board)
it.start()
time.sleep(0.05)
board.analog[0].enable_reporting()

servPin = 8
board.digital[9].write(1)
board.digital[servPin].mode = SERVO

# Equivalente ao void loop();
while True:
    # Pega as informações de temperatura, e precipitação. Está dentro do loop para ser atualizado constantemente.
    temp = r.html.find('span#wob_tm', first=True).text
    prec = r.html.find('div.wtsRwe', first=True).find('span#wob_pp', first=True).text.rstrip("%")
    prec = int(prec)

    # É estúpido mas é necessário. A primeira vez que o sensor é lido, por algum motivo, retorna "None".
    try:
        analog_value = board.analog[0].read()
        time.sleep(0.05)
    except:
        break

    # Lê o sensor e executa os cáculos. O sensor retorna resultados em valor de resistência. Esses
    # cálculos transformam essas informações em porcentagens em consideração da comparação 
    analog_value = board.analog[0].read()
    moistData = analog_value * 1000
    moistCalc = int(100 - ((moistData/1023)*100))

    # Simples declarações de "Se" para executar as comparações
    if moistCalc <= 45 and prec <= 70:
        # Gira o Servo para ligar a torneira
        board.digital[servPin].write(180) # Torneira ON
        # Liga o Relé no pino 9
        board.digital[9].write(0)
        msg = "Torneira LIG."
    else: 
        # Gira o Servo para desligar a torneira
        board.digital[servPin].write(0) # Torneira OFF
        # Desliga o relé no pino 9
        board.digital[9].write(1)
        msg = "Torneira DES."

    # É necessário de definir valores para "string" para que possam ser mostrados no display
    data1 = "Precipit.: " + str(prec) + "%"
    data2 = "Temp: " + str(temp) + " C"
    data3 = "Hum. Sensor: " + str(moistCalc) + "%"
    data4 = msg

    # Mostra no console
    print(title)
    print(prec,"%"," de precipitação")
    print(moistCalc, "%", " humidade no sensor")
    print("Status torneira: ", msg)
    print("\nCTRL+C to terminate program.")
    # LCD
    board.send_sysex(STRING_DATA, util.str_to_two_byte_iter(data1))
    board.send_sysex(STRING_DATA, util.str_to_two_byte_iter(data2))
    time.sleep(5)
    board.send_sysex(STRING_DATA, util.str_to_two_byte_iter(data3))
    board.send_sysex(STRING_DATA, util.str_to_two_byte_iter(data4))
    # Limpa o console
    time.sleep(5)
    clearConsole()