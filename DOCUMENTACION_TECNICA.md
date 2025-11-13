# Documentación Técnica - Simulador de Sistemas Operativos

## 📐 Especificaciones Técnicas

### Memoria

#### Configuración por Defecto
- **Tamaño total**: 550KB
- **Sistema Operativo**: 100KB (reservado, direcciones 0-99)
- **Particiones de usuario**:
  - Partición 1: 250KB (direcciones 100-349)
  - Partición 2: 150KB (direcciones 350-499)
  - Partición 3: 50KB (direcciones 500-549)

#### Algoritmo de Asignación: Best-Fit

**Ventajas:**
- Minimiza la fragmentación interna
- Utiliza eficientemente el espacio disponible

**Desventajas:**
- Requiere búsqueda completa de todas las particiones
- Puede dejar fragmentos muy pequeños inutilizables

**Complejidad temporal**: O(n) donde n es el número de particiones

### Planificación de Procesos

#### Algoritmo: SRTF (Shortest Remaining Time First)

**Características:**
- **Tipo**: Preemptive (con preemption)
- **Criterio de selección**: Menor tiempo restante de ejecución
- **Objetivo**: Minimizar tiempo de espera promedio

**Ventajas:**
- Óptimo para minimizar tiempo de espera promedio
- Procesos cortos se ejecutan rápidamente
- Mejor utilización de CPU

**Desventajas:**
- Requiere conocimiento del tiempo de ejecución
- Puede causar inanición (starvation) de procesos largos
- Overhead por cambios de contexto frecuentes

**Complejidad temporal**: O(n log n) para selección (con ordenamiento)

### Estados de Procesos

```
┌─────────┐
│   NEW   │ ──(llega al sistema)──┐
└─────────┘                        │
                                   │
┌─────────┐                        │
│  READY  │ ◄──────────────────────┘
└─────────┘                        │
    │                              │
    │ (seleccionado por scheduler) │
    ▼                              │
┌─────────────┐                    │
│ EXECUTING   │                    │
└─────────────┘                    │
    │                              │
    │ (termina)                    │
    ▼                              │
┌─────────────┐                    │
│ TERMINATED  │                    │
└─────────────┘                    │
                                   │
┌─────────────┐                    │
│  SUSPENDED  │ ◄──────────────────┘
└─────────────┘
    (no cabe en memoria o excede DOM)
```

### Grado de Multiprogramación (DOM)

El grado de multiprogramación limita el número máximo de procesos que pueden estar simultáneamente en memoria (en estado Ready o Executing).

**Fórmula:**
```
DOM = |Ready Queue| + |Executing Process|
```

Si `DOM >= degree_of_multiprogramming`, los nuevos procesos van a la cola de suspendidos.

## 🔄 Flujo de Ejecución

### Ciclo Principal de Simulación

```
INICIO
  │
  ├─► 1. Llegada de nuevos procesos (arrival_time == clock)
  │     │
  │     ├─► Intentar asignar memoria (Best-Fit)
  │     │     │
  │     │     ├─► Éxito → Estado READY
  │     │     └─► Falla → Estado SUSPENDED
  │     │
  │     └─► Verificar grado de multiprogramación
  │
  ├─► 2. Intentar cargar procesos suspendidos
  │     │
  │     └─► Si hay espacio (DOM < límite) → Intentar asignar memoria
  │
  ├─► 3. Planificación (SRTF)
  │     │
  │     ├─► Verificar preemption
  │     │     │
  │     │     └─► Si hay proceso con menor tiempo restante → Preemptar
  │     │
  │     └─► Seleccionar siguiente proceso (menor tiempo restante)
  │
  ├─► 4. Actualizar tiempos de espera
  │     │
  │     └─► Solo para procesos que NO se han ejecutado por primera vez
  │
  ├─► 5. Ejecutar tick
  │     │
  │     ├─► Decrementar remaining_time del proceso en ejecución
  │     │
  │     └─► Si remaining_time == 0 → Terminar proceso
  │
  ├─► 6. Mostrar estado (si llegó proceso nuevo o terminó uno)
  │
  └─► 7. Incrementar clock
       │
       └─► Repetir hasta que todos los procesos terminen
```

## 📊 Cálculo de Estadísticas

### Tiempo de Retorno (Turnaround Time)

```
Turnaround Time = Finish Time - Arrival Time
```

Representa el tiempo total que el proceso estuvo en el sistema.

### Tiempo de Espera (Wait Time)

```
Wait Time = First Execution Time - Arrival Time
```

Representa el tiempo que el proceso esperó antes de ejecutarse por primera vez.

**Nota**: El tiempo de espera solo se cuenta hasta la primera ejecución. Una vez que el proceso se ejecuta, no se acumula más tiempo de espera, incluso si es preemptado.

### Rendimiento (Throughput)

```
Throughput = Número de procesos terminados / Tiempo total de simulación
```

Mide la cantidad de procesos completados por unidad de tiempo.

## 🎯 Casos de Uso y Escenarios

### Escenario 1: Proceso que no cabe en memoria

**Situación**: Proceso con tamaño mayor que todas las particiones disponibles.

**Comportamiento**:
- El proceso se marca como SUSPENDED
- Permanecerá en la cola de suspendidos durante toda la simulación
- No se ejecutará nunca
- Aparecerá en estadísticas con "N/A" en tiempos de fin y retorno

### Escenario 2: Preemption con SRTF

**Situación**: Proceso A ejecutándose con tiempo restante 5. Llega proceso B con tiempo restante 2.

**Comportamiento**:
1. Proceso B llega y se asigna a memoria
2. Scheduler detecta que B tiene menor tiempo restante
3. Se hace preemption: A vuelve a READY, B comienza ejecución
4. B ejecuta hasta completarse
5. A continúa su ejecución

### Escenario 3: Fragmentación Interna

**Situación**: Proceso de 80KB asignado a partición de 250KB.

**Resultado**:
- Fragmentación interna = 250KB - 80KB = 170KB
- Este espacio no puede ser utilizado por otros procesos
- Se muestra en la tabla de memoria

### Escenario 4: Grado de Multiprogramación

**Situación**: DOM = 5, hay 5 procesos en Ready, llega un nuevo proceso.

**Comportamiento**:
- El nuevo proceso no puede entrar a Ready (DOM >= límite)
- Se marca como SUSPENDED
- Esperará hasta que un proceso termine y libere espacio

## 🔍 Detalles de Implementación

### Gestión de Memoria

#### Clase `MemoryManager`

```python
class MemoryManager:
    def find_best_fit(self, process: Process) -> Optional[Partition]:
        """
        Encuentra la mejor partición usando Best-Fit.
        
        Algoritmo:
        1. Filtrar particiones libres que puedan contener el proceso
        2. Seleccionar la que tenga menor fragmentación interna
        3. Retornar None si no hay partición disponible
        """
```

#### Clase `Partition`

```python
class Partition:
    def assign_process(self, process: Process) -> bool:
        """
        Asigna un proceso a la partición.
        
        Validaciones:
        - Partición debe estar libre
        - Tamaño de partición >= tamaño del proceso
        
        Efectos:
        - Actualiza fragmentación interna
        - Establece referencia bidireccional (partition ↔ process)
        """
```

### Planificación

#### Clase `Scheduler`

```python
class Scheduler:
    def select_next_process(self, ready_queue: List[Process]) -> Optional[Process]:
        """
        Selecciona proceso con menor tiempo restante (SRTF).
        
        Algoritmo:
        - Encontrar proceso con mínimo remaining_time
        - Retornar None si la cola está vacía
        """
    
    def should_preempt(self, ready_queue: List[Process]) -> bool:
        """
        Determina si se debe hacer preemption.
        
        Condición:
        - Existe proceso en ready_queue con remaining_time < current_process.remaining_time
        """
```

### Simulación

#### Clase `Simulator`

**Colas de Procesos**:
- `all_processes`: Procesos que aún no han llegado (arrival_time > clock)
- `new_queue`: Procesos que llegaron pero aún no se procesaron
- `ready_queue`: Procesos en memoria, listos para ejecutar
- `suspended_queue`: Procesos suspendidos (no en memoria)
- `terminated_queue`: Procesos finalizados

**Eventos**:
- `new_process_arrived`: Flag que indica llegada de nuevo proceso
- `process_finished`: Flag que indica finalización de proceso

**Visualización**:
- Se muestra estado solo cuando ocurre un evento (llegada o finalización)
- Esto evita salida excesiva y permite análisis paso a paso

## 🧮 Ejemplos de Cálculo

### Ejemplo 1: Tiempo de Espera

**Proceso**:
- Arrival Time: 0
- Burst Time: 5
- First Execution Time: 2

**Cálculo**:
```
Wait Time = 2 - 0 = 2 unidades de tiempo
```

### Ejemplo 2: Tiempo de Retorno

**Proceso**:
- Arrival Time: 0
- Finish Time: 7

**Cálculo**:
```
Turnaround Time = 7 - 0 = 7 unidades de tiempo
```

### Ejemplo 3: Throughput

**Simulación**:
- Procesos terminados: 10
- Tiempo total: 50 unidades

**Cálculo**:
```
Throughput = 10 / 50 = 0.2 procesos/unidad de tiempo
```




## 📝 Notas de Implementación

### Decisiones de Diseño

1. **Arquitectura Monolítica**: Todo el código está en un solo archivo para facilitar la comprensión y el mantenimiento del TPI.

2. **Separación de Responsabilidades**: Aunque está en un archivo, el código está organizado en módulos lógicos (Enums, Modelos, Servicios, UI, Simulador).

3. **Manejo de Errores**: Validaciones en lectura de archivos y asignación de memoria para evitar errores en tiempo de ejecución.

4. **Visualización Opcional**: Uso de `tabulate` es opcional, con fallback a visualización básica si no está instalado.

5. **Tiempo de Espera**: Se calcula desde la llegada hasta la primera ejecución, no incluye tiempo de espera después de preemption.

---

**Versión**: 1.0  
**Fecha**: 2025

