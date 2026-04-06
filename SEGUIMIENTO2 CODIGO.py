# Importacion de las librerias
from machine import Pin, PWM, ADC
import time

# Definicion de las entradas y de los bits
adc1 = ADC(Pin(34)) #potenciometro 1
adc1.width(ADC.WIDTH_12BIT) #bit de 12 4095
adc2 = ADC(Pin(35)) #potenciometro 2
adc2.width(ADC.WIDTH_10BIT) #bit de 10 1023
btn_automatico = Pin(25, Pin.IN, Pin.PULL_UP) # boton negro para la secuencia automatica
btn_secuencia = Pin(26, Pin.IN, Pin.PULL_UP) # boton rojo para la secuencia aleatoria

# Definicion de las salidas de la esp
servo1 = PWM(Pin(15), freq=50)
servo2 = PWM(Pin(2), freq=50)
led_verde = Pin(12, Pin.OUT)
led_rojo = Pin(14, Pin.OUT)
buzzer = PWM(Pin(27))

# Variables
modo = "manual"
ultima_interrupcion = 0
# angulos iniciales de los servos y angulos que se tienen en cuenta para todo mas adelante
angulo1 = 90 
angulo2 = 90

# Funcion para mover los servos y definir el rango de movimiento de ellos 
def mover_servo(servo, angulo):

    if servo == servo1:
        min_duty = 20
        max_duty = 120
    else:
        min_duty = 20
        max_duty = 120

    duty = min_duty + (angulo / 180) * (max_duty - min_duty)
    servo.duty(int(duty))


# Esta funcion ayuda a que los servos se muevan al mismo tiempo los dos

def mover_suave(inicio1, fin1, inicio2, fin2):
    global modo

    pasos = max(abs(int(fin1 - inicio1)), abs(int(fin2 - inicio2)))

    for i in range(pasos):

        # permite el cambio de un modo a otro
        if modo != "reset" and modo != "secuencia":
            break

        ang1 = inicio1 + (fin1 - inicio1) * i / pasos
        ang2 = inicio2 + (fin2 - inicio2) * i / pasos

        mover_servo(servo1, ang1)
        mover_servo(servo2, ang2)

        time.sleep_ms(8) 

# configuracion del buzzer porque es pasivo

def buzzer_on(freq=1000):
    buzzer.freq(freq)
    buzzer.duty(512)

def buzzer_off():
    buzzer.duty(0)

def beep_corto():
    buzzer_on(1500)
    time.sleep(0.2)
    buzzer_off()


# definicion de las interrupciones como el antirebote y la interupcion de la funcion

def interrupcion_reset(pin):
    global modo, ultima_interrupcion
    ahora = time.ticks_ms()

    # modo antirebote 
    if time.ticks_diff(ahora, ultima_interrupcion) > 100:
        modo = "reset"
        ultima_interrupcion = ahora

def interrupcion_secuencia(pin):
    global modo, ultima_interrupcion
    ahora = time.ticks_ms()

    if time.ticks_diff(ahora, ultima_interrupcion) > 100:
        modo = "secuencia"
        ultima_interrupcion = ahora


btn_automatico.irq(trigger=Pin.IRQ_FALLING, handler=interrupcion_reset)
btn_secuencia.irq(trigger=Pin.IRQ_FALLING, handler=interrupcion_secuencia)

#codigo de funcionamiento donde estan almacendas las funciones

while True:

    # Definicion del modo manual
    if modo == "manual":

        led_verde.value(1)
        led_rojo.value(0)
        buzzer_off()

        raw1 = adc1.read() #lee en que valor de bit esta en realidad el potenciometro
        raw2 = adc2.read()
        
        angulo1 = raw1 / 4095 * 180 #este es el servo 1 de 12 bits 
        angulo2 = raw2 / 1023 * 180 #este es el servo 2 de 10 bits
        

        mover_servo(servo1, angulo1)
        mover_servo(servo2, angulo2)

        print("Manual:", angulo1, angulo2)

    # Definicion del modo automatico/reset en el que los servos se mueven y llegan al punto inicial

    elif modo == "reset":

        led_verde.value(0)
        led_rojo.value(1)
        buzzer_on(100)

        print("Reset con movimiento controlado")
    # se decretan una serie de pasos para que el reset sea mas evidente
    # el primer paso es que va hasta noventa
        mover_suave(angulo1, 90, angulo2, 90)
        if modo != "reset": continue
    # el paso dos es que ahora los dos van de 90 a 0 grados
        mover_suave(90, 0, 90, 0)
        if modo != "reset": continue
    # y como paso final de pasar de estar de 90 van a 0
        mover_suave(0, 90, 0, 90)
        if modo != "reset": continue

        angulo1 = 90
        angulo2 = 90

        buzzer_off()
        modo = "manual"

    # Aqui se define el modo de secuencia donde se les dan unos angulos y ellos se 
    # mueven individualmente
    elif modo == "secuencia":

        led_verde.value(0)
        led_rojo.value(1)

        beep_corto()

        print("Ejecutando secuencia")

        mover_suave(angulo1, 0, angulo2, 150)
        if modo != "secuencia": continue

        mover_suave(0, 180, 150, 0)
        if modo != "secuencia": continue

        mover_suave(180, 40, 0, 180)
        if modo != "secuencia": continue

        mover_suave(40, angulo1, 180, angulo2)
        if modo != "secuencia": continue

        modo = "manual"

    time.sleep_ms(30)