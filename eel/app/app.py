import eel
from enum import Enum
import numpy as np
import math as mt
import json
class SERVER_STATUS(Enum):
    DISPONIBLE = 0
    OCUPADO = 1

class EVENT_TYPE(Enum):
    ARRRIBO = "A"
    PARTIDA = "P"
    UNKNOWN = ""

# Sitema MM1
class Sim:
    def __init__(self,codigo,serverEstatus,
                nextEvent,clock,
                totalDelay,timeServiceacumulated,
                areaQ,areaB,
                timeOfLastEvent,numberOfClientsInQueue,
                numberOfClientsCompletedWithDelay,
                number,
                midTimeArrivals,
                midTimeService): 
        self.codigo=codigo or 0
        self.serverEstatus = serverEstatus or SERVER_STATUS.DISPONIBLE.value
        self.nextEvent = nextEvent or ""
        self.clock = clock or 0.0
        self.totalDelay = totalDelay or 0.0
        self.timeServiceacumulated = timeServiceacumulated or 0.0
        self.areaQ = areaQ or 0.0
        self.areaB = areaB or 0.0
        self.timeOfLastEvent = timeOfLastEvent or 0.0 
        self.numberOfClientsInQueue = numberOfClientsInQueue or 0
        self.numberOfClientsCompletedWithDelay = numberOfClientsCompletedWithDelay or 0.0
        self.midTimeArrivals = midTimeArrivals or 0.0
        self.midTimeService = midTimeService or 0.0
        self.eventList = []
        self.queue = []
        #Listas para generar las gráficas
        self.clientQueueinT = []
        self.clockinT = []
        self.tsAcuminT = []
        #Tiempo del primer arribo
        self.eventList.append(np.random.exponential(1/self.midTimeArrivals))
        self.simulationEnded = False
        #Le pongo un número grande para asegurarme que el primer evento sea un arribo
        self.eventList.append(number)

    def getTimeEvent(self):
        self.timeOfLastEvent = self.clock
        if self.eventList[0] <= self.eventList[1]:
            self.clock = self.eventList[0]
            self.nextEvent = EVENT_TYPE.ARRRIBO.value
        else:
            self.clock = self.eventList[1]
            self.nextEvent = EVENT_TYPE.PARTIDA.value

    def arrival(self):
        #Todo arribo desencadena un nuevo arribo
        self.eventList[0] = self.clock + np.random.exponential(1/self.midTimeArrivals)
        #Pregunto si el servidor está disponible
        if self.serverEstatus == SERVER_STATUS.DISPONIBLE.value:

            # Cambio el servidor al estado Ocupado
            self.serverEstatus = SERVER_STATUS.OCUPADO.value

            # Programo el próximo evento partida
            self.eventList[1] = self.clock + np.random.exponential(1/self.midTimeService)
            
            #Acumulo el tiempo de servicio
            self.timeServiceacumulated += (self.eventList[1] - self.clock)

            #Actualizo la cantidad de clientes que completaron la demora
            self.numberOfClientsCompletedWithDelay += 1

            #-----------Gráficas---------------
            self.clockinT.append(self.clock)
            self.clientQueueinT.append(self.numberOfClientsInQueue)
            self.tsAcuminT.append(self.timeServiceacumulated)
            
        else:
            #Calculo área bajo Q(t) desde el momento actual del reloj hacia atrás (tiempo del último evento)
            self.areaQ += (self.numberOfClientsInQueue * (self.clock - self.timeOfLastEvent))     

            #Incremento la cantidad de clientes en cola en 1       
            self.numberOfClientsInQueue +=1

            #Guardo el valor del reloj en la posición "Nro de Clientes en cola" para saber
            #cuando llegó el cliente a la cola y más adelante calcular la demora
            self.queue.append(self.clock)

            #--------- Gráficas---------------------
            self.clockinT.append(self.clock)
            self.clientQueueinT.append(self.numberOfClientsInQueue)
            self.tsAcuminT.append(self.timeServiceacumulated)            

    
    def departure(self):
        #Pregunto si hay clientes en cola 
        if self.numberOfClientsInQueue > 0:
            #Tiempo del próximo evento partida
            self.eventList[1] = self.clock + np.random.exponential(1/self.midTimeService)
            #Acumulo la la demora acumulada como el valor actual del reloj menos el valor del
            # reloj cuando el cliente ingresó a la cola
            self.totalDelay += self.clock - self.queue[0]

            #Actualizo el contador de clientes que completaron demora
            self.numberOfClientsCompletedWithDelay += 1

            #Acumulo el tiempo de servicio
            self.timeServiceacumulated += (self.eventList[1] - self.clock)

            #Calculo el área bajo Q(t) del período anterior (Reloj - Tiempo del último evento)
            self.areaQ += (self.numberOfClientsInQueue * (self.clock - self.timeOfLastEvent))

            #Decremento la cantidad de clientes en cola en uno
            self.numberOfClientsInQueue -= 1

            #Voy a desplazar a los valores de la cola un lugar hacia arriba
            self.queue.pop(0)

            #----------- Gráfcias ----------------
            self.clockinT.append(self.clock)
            self.clientQueueinT.append(self.numberOfClientsInQueue)
            self.tsAcuminT.append(self.timeServiceacumulated)
           
        else:
            #Si no hay clientes en la cola, establezco el estado del servidor en "Disponible"
            self.serverEstatus = SERVER_STATUS.DISPONIBLE.value

            #Forzar a que no haya partidas si no hay clientes atendiendo
            self.eventList[1] = 99999999

            #----------- Gráficas ----------------
            self.clockinT.append(self.clock)
            self.clientQueueinT.append(self.numberOfClientsInQueue)
            self.tsAcuminT.append(self.timeServiceacumulated)
    def changeMidTimeArrivalValue(self,value):
        self.midTimeArrivals = float(value)
    def changeMidTimeServiceValue(self,value):
        self.midTimeService = float(value)
    #Número promedio de clientes en cola
    def getMeanOfClientsInQueue(self):
        if self.clock !=0:
            average_num_of_queued_costumers = self.areaQ/self.clock
            return average_num_of_queued_costumers
        else:
            average_num_of_queued_costumers = 0
            return average_num_of_queued_costumers
    def __repr__(self):
        return """Clock:%s 
        \nClientes en cola:%s
        \nEventos: [ %s , %s ]
        \nProximo evento:%s
        \nAreaDeQ:%s""" % (self.clock,
         self.numberOfClientsInQueue,
         truncate(self.eventList[0],3),
         truncate(self.eventList[1],3),
         "Arribo" if self.nextEvent == EVENT_TYPE.ARRRIBO.value else "Salida",
         self.areaQ)   
    
    # Utilización promedio del servidor
    def getMeanOfServerUtilization(self):
        if self.clock != 0:
            average_server_utilization = self.timeServiceacumulated/self.clock
            return average_server_utilization
        else:
            average_server_utilization = 0
            return average_server_utilization      
        
    # Demora promedio de los clientes
    def getAverageCustomerDelay(self):
        if self.numberOfClientsCompletedWithDelay != 0:
            average_costumers_delay = self.totalDelay/self.numberOfClientsCompletedWithDelay
            return average_costumers_delay
        else:
            average_costumers_delay = 0
            return average_costumers_delay



def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return mt.trunc(stepper * number) / stepper


def main(simulacion):
        simulacion.getTimeEvent()
        if simulacion.nextEvent == EVENT_TYPE.ARRRIBO.value:
            simulacion.arrival()
        else:
            simulacion.departure()
        # if (simulacion.clock > 500):
        #     simulacion.simulationEnded = True
        #     break

@eel.expose()
def animate(midTimeArrival,midTimeService):
    global simulacion,maxClients
    simulacion.changeMidTimeArrivalValue(float(midTimeArrival))
    simulacion.changeMidTimeServiceValue(float(midTimeService))
    main(simulacion)
    xList.append(simulacion.clock)
    yList.append(len(simulacion.queue))
    yList2.append(simulacion.timeServiceacumulated)
    yList3.append(simulacion.getMeanOfServerUtilization() if simulacion.getMeanOfServerUtilization()<=1 else 1)
    eel.print_js({
        'clock':round(simulacion.clock, 2),
        'nextEvent':simulacion.nextEvent,
        'queueSize':len(simulacion.queue),
        'timeServiceAcumulated':simulacion.timeServiceacumulated,
        'meanOfServerUtilization':simulacion.getMeanOfServerUtilization(),
        'nextClockEvents': [ truncate(simulacion.eventList[0],3) , truncate(simulacion.eventList[1],3) ],
        'nextEventType': 'Arribo' if simulacion.nextEvent == EVENT_TYPE.ARRRIBO.value else 'Salida',
        'QArea': truncate(simulacion.areaQ,3),
        'numberOfClientsInQueue':simulacion.numberOfClientsInQueue
        })   

def changeSimState(button,scaleMidTimeArrival,scaleMidTimeService):
    global simStopped
    clockTimeChangeValuesAdd()
    if(simStopped):
        button['text'] = "Parar"
        button['bg'] = "red"
        button['fg'] = "white"
        simStopped = False
        scaleMidTimeService['state'] = "disabled"
        scaleMidTimeArrival['state'] = "disabled"
    else:
        button['text'] = "Iniciar"
        scaleMidTimeService['state'] = "active"
        scaleMidTimeArrival['state'] = "active"
        button['bg'] = "green"
        simStopped = True

def clockTimeChangeValuesAdd():
    global clockTimeChangeValues,simulacion
    if len(clockTimeChangeValues)>1:
        clockTimeChangeValues.append(clockTimeChangeValues[-1]+ simulacion.clock )
    else:
        clockTimeChangeValues.append(simulacion.clock )
        
@eel.expose()
def restartSimulation():
    global a , b , simulacion
    simulacion = Sim(0,SERVER_STATUS.DISPONIBLE.value,EVENT_TYPE.UNKNOWN.value,0.0,0.0,0.0,0.0,0.0,0.0,0,0,99999999,midTimeArrival,midTimeService)
    yList.clear()
    xList.clear()
    yList2.clear()
    yList3.clear()
    clockTimeChangeValues.clear()



midTimeArrival = 8.0
midTimeService = 9.0
maxClients = 15
simStopped = True
xList = []
yList = []
yList2 = []
yList3 = []
clockTimeChangeValues = []


simulacion = Sim(0,SERVER_STATUS.DISPONIBLE.value,EVENT_TYPE.UNKNOWN.value,0.0,0.0,0.0,0.0,0.0,0.0,0,0,99999999,midTimeArrival,midTimeService)


eel.init('carpeta_web_estatica')
eel.start('main_page.html')


