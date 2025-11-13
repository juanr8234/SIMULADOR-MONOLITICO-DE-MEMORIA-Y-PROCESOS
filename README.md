# Simulador de Asignación de Memoria y Planificación de Procesos

## 📋 Descripción

Este proyecto es un simulador monolítico de sistemas operativos que implementa dos componentes fundamentales:

1. **Gestión de Memoria**: Asignación de memoria mediante particiones fijas con algoritmo **Best-Fit**
2. **Planificación de Procesos**: Algoritmo **SRTF (Shortest Remaining Time First)** con preemption

El simulador permite cargar procesos desde archivos CSV, simular su ejecución en un sistema con memoria particionada, y generar estadísticas detalladas sobre el rendimiento del sistema.

## ✨ Características

### Gestión de Memoria
- **Particiones Fijas**: Sistema de memoria con particiones de tamaño fijo
- **Algoritmo Best-Fit**: Asigna procesos a la partición más pequeña que pueda contenerlos, minimizando la fragmentación interna
- **Grado de Multiprogramación**: Controla el número máximo de procesos que pueden estar en memoria simultáneamente
- **Estados de Procesos**: 
  - **New**: Proceso recién llegado al sistema
  - **Ready**: Proceso en memoria, listo para ejecutarse
  - **Executing**: Proceso en ejecución
  - **Suspended**: Proceso suspendido (no cabe en memoria o excede grado de multiprogramación)
  - **Terminated**: Proceso finalizado

### Planificación de Procesos
- **Algoritmo SRTF**: Shortest Remaining Time First (Tiempo Restante Más Corto Primero)
- **Preemption**: Cambio de contexto cuando llega un proceso con menor tiempo restante
- **Colas de Procesos**: Gestión de colas para cada estado del proceso

### Visualización y Estadísticas
- Tabla de distribución de memoria en tiempo real
- Visualización de colas de procesos por estado
- Estadísticas detalladas:
  - Tiempo de arribo
  - Tiempo de irrupción
  - Tiempo de fin
  - Tiempo de retorno (Turnaround Time)
  - Tiempo de espera (Wait Time)
  - Rendimiento del sistema (Throughput)

## 🚀 Requisitos

- Python 3.6 o superior
- Biblioteca `tabulate` (opcional, para mejor visualización de tablas)

## 📦 Instalación

1. Clonar o descargar el repositorio
2. Instalar dependencias (opcional pero recomendado):

```bash
pip install tabulate
```

Si no se instala `tabulate`, el simulador funcionará con una visualización básica.

## 📝 Formato del Archivo CSV

El simulador lee procesos desde archivos CSV con el siguiente formato:

```csv
IDP,TAM,TA,TI
1,100,0,5
2,50,2,3
3,200,4,8
```

**Columnas:**
- **IDP**: Identificador único del proceso
- **TAM**: Tamaño del proceso en KB
- **TA**: Tiempo de arribo (arrival time)
- **TI**: Tiempo de irrupción (burst time)

**Ejemplo de archivo:** Ver `procesos_ejemplo.csv`

## 🎮 Uso

### Ejecutar el Simulador

```bash
python simulador.py
```

### Flujo de Uso

1. **Menú Principal**: Seleccionar "1. Cargar archivo de procesos"
2. **Cargar Archivo**: Ingresar el nombre del archivo CSV (con o sin extensión `.csv`)
3. **Vista Previa**: Revisar los procesos cargados y confirmar
4. **Configuración**:
   - **Grado de Multiprogramación**: Número máximo de procesos en memoria (default: 5)
   - **Particiones de Memoria**: 
     - Opción 1: Configuración del TP (250K, 150K, 50K) - **POR DEFECTO**
     - Opción 2: Configuración alternativa (60K, 120K, 250K)
     - Opción 3: Personalizada (definir manualmente)
5. **Simulación**: El simulador mostrará el estado del sistema cada vez que:
   - Llega un nuevo proceso
   - Termina un proceso en ejecución
6. **Estadísticas Finales**: Al finalizar, se muestra un informe estadístico completo

### Configuración de Memoria

El sistema reserva **100KB para el Sistema Operativo**. Las particiones por defecto son:

- **Partición 1**: 250KB (inicio en dirección 100)
- **Partición 2**: 150KB (inicio en dirección 350)
- **Partición 3**: 50KB (inicio en dirección 500)

**Total de memoria**: 550KB (100KB SO + 450KB para procesos)

## 📊 Salida del Simulador

### Durante la Simulación

El simulador muestra en cada evento:

1. **Tiempo Actual**: Reloj del sistema
2. **Distribución de Memoria**: Tabla con:
   - Partición
   - Tamaño
   - Proceso asignado (o "Libre")
   - Fragmentación interna
3. **Colas de Procesos**: Procesos organizados por estado:
   - Ejecución
   - Listo
   - Listo/Suspendido
   - Nuevo
   - Terminado

### Estadísticas Finales

Al finalizar la simulación, se muestra:

- **Tabla de Procesos**: Con tiempos de arribo, irrupción, fin, retorno y espera
- **Promedios**: Tiempo de retorno promedio y tiempo de espera promedio
- **Rendimiento**: Procesos por unidad de tiempo (throughput)

## 🔧 Arquitectura del Código

### Estructura del Proyecto

```
simulador.py
├── Enums
│   └── ProcessState: Estados de los procesos
├── Modelos
│   ├── Process: Representa un proceso
│   └── Partition: Representa una partición de memoria
├── Servicios
│   ├── FileReader: Lectura de archivos CSV
│   ├── MemoryManager: Gestión de memoria (Best-Fit)
│   └── Scheduler: Planificación SRTF
├── Interfaz de Usuario
│   ├── Display: Visualización de información
│   └── Menu: Menú interactivo
└── Simulador
    └── Simulator: Motor principal de simulación
```

### Componentes Principales

#### `Process`
Representa un proceso con:
- Identificador, tamaño, tiempos de arribo e irrupción
- Estado actual y tiempo restante
- Estadísticas (tiempo de espera, turnaround, etc.)

#### `Partition`
Representa una partición de memoria con:
- Identificador, tamaño y dirección de inicio
- Proceso asignado (si hay)
- Fragmentación interna

#### `MemoryManager`
Gestiona la asignación de memoria:
- `find_best_fit()`: Encuentra la mejor partición usando Best-Fit
- `allocate_process()`: Asigna un proceso a memoria
- `free_process()`: Libera memoria de un proceso

#### `Scheduler`
Planifica la ejecución de procesos:
- `select_next_process()`: Selecciona el proceso con menor tiempo restante (SRTF)
- `should_preempt()`: Determina si se debe hacer preemption
- `execute_tick()`: Ejecuta una unidad de tiempo

#### `Simulator`
Motor principal que coordina:
- Llegada de procesos
- Asignación de memoria
- Planificación y ejecución
- Visualización de estado

## 📈 Algoritmos Implementados

### Best-Fit (Mejor Ajuste)

El algoritmo Best-Fit busca la partición más pequeña que pueda contener el proceso, minimizando la fragmentación interna.

**Pseudocódigo:**
```
best_partition = None
min_fragmentation = ∞

para cada partición en particiones:
    si partición está libre y partición.tamaño >= proceso.tamaño:
        fragmentación = partición.tamaño - proceso.tamaño
        si fragmentación < min_fragmentation:
            min_fragmentation = fragmentación
            best_partition = partición

retornar best_partition
```

### SRTF (Shortest Remaining Time First)

El algoritmo SRTF siempre ejecuta el proceso con el menor tiempo restante. Si llega un proceso con menor tiempo restante que el actual, se hace preemption.

**Características:**
- Preemptive: Puede interrumpir un proceso en ejecución
- Óptimo para minimizar tiempo de espera promedio
- Requiere estimación precisa del tiempo de ejecución

## 🧪 Ejemplos de Uso

### Ejemplo 1: Proceso Simple

**Archivo CSV:**
```csv
IDP,TAM,TA,TI
1,100,0,5
```

**Resultado esperado:**
- Proceso 1 llega en tiempo 0
- Se asigna a partición 1 (250KB)
- Ejecuta durante 5 unidades de tiempo
- Termina en tiempo 5

### Ejemplo 2: Múltiples Procesos con Preemption

**Archivo CSV:**
```csv
IDP,TAM,TA,TI
1,50,0,10
2,30,3,2
```

**Resultado esperado:**
- Proceso 1 llega en tiempo 0, comienza ejecución
- Proceso 2 llega en tiempo 3 con TI=2 (menor que el tiempo restante de P1)
- Se hace preemption: P1 vuelve a Ready, P2 ejecuta
- P2 termina en tiempo 5
- P1 continúa ejecutándose hasta tiempo 13

## 🐛 Solución de Problemas

### Error: "El archivo no existe"
- Verificar que el archivo CSV esté en el mismo directorio que `simulador.py`
- Verificar que el nombre del archivo sea correcto (con o sin extensión `.csv`)

### Error: "No se pudieron cargar procesos"
- Verificar el formato del CSV (debe tener cabecera: IDP,TAM,TA,TI)
- Verificar que cada fila tenga exactamente 4 valores
- Verificar que los valores sean numéricos válidos

### Procesos no se ejecutan
- Verificar que el tamaño del proceso no exceda el tamaño de ninguna partición
- Verificar el grado de multiprogramación (puede estar limitando la cantidad de procesos)

## 📚 Referencias

- Sistemas Operativos Modernos - Andrew S. Tanenbaum
- Operating System Concepts - Silberschatz, Galvin, Gagne

## 👥 Autor

Desarrollado como Trabajo Práctico Integrador (TPI) de Sistemas Operativos.

## 📄 Licencia

Este proyecto es de uso educativo.

---

**Versión**: Monolítica (Todo el código en un solo archivo)  
**Última actualización**: 2024

