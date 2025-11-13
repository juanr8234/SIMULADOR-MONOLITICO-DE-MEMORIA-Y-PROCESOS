"""
Simulador de Asignación de Memoria y Planificación de Procesos
Versión Monolítica - Todo el código en un solo archivo
"""

import csv
import os
import sys
from enum import Enum
from typing import List, Optional


# ============================================================================
# ENUMS
# ============================================================================

class ProcessState(Enum):
    """Estados posibles de un proceso."""
    NEW = "New"
    READY = "Ready"
    EXECUTING = "Executing"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"


# ============================================================================
# MODELOS
# ============================================================================

class Process:
    """Representa un proceso en el simulador."""
    
    def __init__(self, id: int, size: int, arrival_time: int, burst_time: int):
        """
        Inicializa un proceso.
        
        Args:
            id: Identificador único del proceso
            size: Tamaño en KB que ocupa en memoria
            arrival_time: Tiempo de arribo al sistema
            burst_time: Tiempo de irrupción (duración de ejecución)
        """
        self.id = int(id)
        self.size = int(size)
        self.arrival_time = int(arrival_time)
        self.burst_time = int(burst_time)
        
        # Estado inicial
        self.state = ProcessState.NEW
        self.remaining_time = int(burst_time)
        self.partition = None
        
        # Estadísticas
        self.wait_time = 0
        self.finish_time = 0
        self.turnaround_time = 0
        self.first_execution_time = None  # Tiempo en que se ejecuta por primera vez
    
    @property
    def state_str(self) -> str:
        """Retorna el estado como string."""
        return self.state.value
    
    def calculate_statistics(self):
        """
        Calcula las estadísticas del proceso al terminar.
        Tiempo de espera = Tiempo desde que llega hasta que entra al procesador por primera vez
        """
        self.turnaround_time = self.finish_time - self.arrival_time
        
        # Calcular tiempo de espera: desde que llega hasta que se ejecuta por primera vez
        if self.first_execution_time is not None:
            # Tiempo de espera = Tiempo de primera ejecución - Tiempo de arribo
            self.wait_time = self.first_execution_time - self.arrival_time
        else:
            # Si nunca se ejecutó, usar la fórmula estándar
            # (pero esto no debería pasar para procesos terminados)
            self.wait_time = self.turnaround_time - self.burst_time
    
    def __repr__(self):
        """Representación legible del proceso."""
        return (f"Process(id={self.id}, size={self.size}K, "
                f"arrival={self.arrival_time}, burst={self.burst_time}, "
                f"state={self.state_str})")


class Partition:
    """Representa una partición de memoria fija."""
    
    def __init__(self, id: int, size: int, start_address: int):
        """
        Inicializa una partición de memoria.
        
        Args:
            id: Identificador único de la partición
            size: Tamaño de la partición en KB
            start_address: Dirección de inicio en memoria
        """
        self.id = int(id)
        self.size = int(size)
        self.start_address = int(start_address)
        self.process: Optional[Process] = None
        self.internal_fragmentation = 0
    
    def is_free(self) -> bool:
        """Verifica si la partición está libre."""
        return self.process is None
    
    def assign_process(self, process: Process) -> bool:
        """
        Asigna un proceso a esta partición.
        
        Args:
            process: Proceso a asignar
            
        Returns:
            True si se asignó correctamente, False en caso contrario
        """
        if not self.is_free():
            return False
        
        if self.size < process.size:
            return False
        
        self.process = process
        self.internal_fragmentation = self.size - process.size
        process.partition = self
        return True
    
    def free(self) -> Optional[Process]:
        """
        Libera la partición y retorna el proceso que estaba asignado.
        
        Returns:
            El proceso que estaba asignado, o None si estaba libre
        """
        if self.is_free():
            return None
        
        freed_process = self.process
        self.process.partition = None
        self.process = None
        self.internal_fragmentation = 0
        return freed_process
    
    def __repr__(self):
        """Representación legible de la partición."""
        process_id = self.process.id if self.process else "Libre"
        return (f"Partition(id={self.id}, size={self.size}K, "
                f"start={self.start_address}, process={process_id}, "
                f"frag={self.internal_fragmentation}K)")


# ============================================================================
# SERVICIOS
# ============================================================================

class FileReader:
    """Maneja la lectura de procesos desde archivos CSV."""
    
    @staticmethod
    def read_processes(filename: str, max_processes: int = 10) -> Optional[List[Process]]:
        """
        Lee procesos desde un archivo CSV.
        
        Args:
            filename: Nombre del archivo CSV
            max_processes: Número máximo de procesos a cargar
            
        Returns:
            Lista de procesos o None si hubo un error
        """
        if not os.path.exists(filename):
            print(f"Error: El archivo '{filename}' no existe.")
            return None
        
        processes = []
        
        try:
            with open(filename, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                # Omitir cabecera
                try:
                    next(reader)
                except StopIteration:
                    print(f"Error: El archivo '{filename}' está vacío.")
                    return []
                
                # Leer procesos
                for row in reader:
                    if len(row) == 4 and len(processes) < max_processes:
                        try:
                            process = Process(
                                id=row[0],
                                size=row[1],
                                arrival_time=row[2],
                                burst_time=row[3]
                            )
                            processes.append(process)
                        except (ValueError, IndexError) as e:
                            print(f"Error: Fila inválida omitida: {row} - {e}")
                            continue
                    elif len(processes) >= max_processes:
                        print(f"Advertencia: Límite de {max_processes} procesos alcanzado.")
                        break
                    elif row:  # Fila no vacía pero mal formada
                        print(f"Advertencia: Fila omitida (formato inválido): {row}")
            
            if not processes:
                print(f"Error: No se pudieron cargar procesos del archivo '{filename}'.")
                return None
            
            # Ordenar por tiempo de arribo
            processes.sort(key=lambda p: p.arrival_time)
            print(f"✓ Se cargaron {len(processes)} procesos exitosamente.")
            return processes
            
        except IOError as e:
            print(f"Error de E/S al leer el archivo: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al leer el archivo: {e}")
            return None
    
    @staticmethod
    def preview_processes(processes: List[Process]) -> None:
        """
        Muestra una vista previa de los procesos cargados.
        
        Args:
            processes: Lista de procesos a mostrar
        """
        try:
            from tabulate import tabulate
            
            headers = ["IDP", "TAM", "TA", "TI"]
            table_data = []
            
            for process in processes:
                table_data.append([
                    process.id,
                    f"{process.size}K",
                    process.arrival_time,
                    process.burst_time
                ])
            
            print("\n" + "="*50)
            print("VISTA PREVIA DE PROCESOS")
            print("="*50)
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print("="*50 + "\n")
            
        except ImportError:
            # Fallback si tabulate no está instalado
            print("\n" + "="*50)
            print("VISTA PREVIA DE PROCESOS")
            print("="*50)
            print(f"{'IDP':<5} {'TAM':<8} {'TA':<5} {'TI':<5}")
            print("-"*50)
            for process in processes:
                print(f"{process.id:<5} {process.size:<8}K {process.arrival_time:<5} {process.burst_time:<5}")
            print("="*50 + "\n")


class MemoryManager:
    """Gestiona la asignación de memoria usando particiones fijas y algoritmo Best-Fit."""
    
    def __init__(self, partitions: List[Partition]):
        """
        Inicializa el gestor de memoria.
        
        Args:
            partitions: Lista de particiones de memoria disponibles
        """
        self.partitions = partitions
    
    def find_best_fit(self, process: Process) -> Optional[Partition]:
        """
        Encuentra la mejor partición para un proceso usando Best-Fit.
        
        Args:
            process: Proceso a asignar
            
        Returns:
            La mejor partición o None si no hay espacio disponible
        """
        best_partition = None
        min_fragmentation = float('inf')
        
        for partition in self.partitions:
            if partition.is_free() and partition.size >= process.size:
                fragmentation = partition.size - process.size
                if fragmentation < min_fragmentation:
                    min_fragmentation = fragmentation
                    best_partition = partition
        
        return best_partition
    
    def allocate_process(self, process: Process) -> bool:
        """
        Asigna un proceso a memoria usando Best-Fit.
        
        Args:
            process: Proceso a asignar
            
        Returns:
            True si se asignó correctamente, False en caso contrario
        """
        partition = self.find_best_fit(process)
        
        if partition is None:
            return False
        
        # Si la partición ya tiene un proceso, lo movemos a disco (suspendido)
        if not partition.is_free():
            old_process = partition.free()
            if old_process:
                old_process.state = ProcessState.SUSPENDED
                old_process.partition = None
        
        # Asignar el nuevo proceso
        partition.assign_process(process)
        process.state = ProcessState.READY
        return True
    
    def free_process(self, process: Process) -> None:
        """
        Libera la memoria ocupada por un proceso.
        
        Args:
            process: Proceso a liberar
        """
        if process.partition:
            process.partition.free()
            process.partition = None
    
    def get_memory_status(self) -> List[dict]:
        """
        Obtiene el estado actual de la memoria.
        
        Returns:
            Lista de diccionarios con información de cada partición
        """
        status = []
        for partition in self.partitions:
            status.append({
                'id': partition.id,
                'size': partition.size,
                'start_address': partition.start_address,
                'process_id': partition.process.id if partition.process else None,
                'internal_fragmentation': partition.internal_fragmentation,
                'free': partition.is_free()
            })
        return status


class Scheduler:
    """Planifica la ejecución de procesos usando SRTF."""
    
    def __init__(self):
        """Inicializa el planificador SRTF."""
        self.current_process: Optional[Process] = None
    
    def select_next_process(self, ready_queue: List[Process]) -> Optional[Process]:
        """
        Selecciona el siguiente proceso a ejecutar usando SRTF.
        Elige el proceso con menor tiempo restante.
        
        Args:
            ready_queue: Cola de procesos listos
            
        Returns:
            El proceso seleccionado o None si la cola está vacía
        """
        if not ready_queue:
            return None
        
        # SRTF: Shortest Remaining Time First
        return min(ready_queue, key=lambda p: p.remaining_time)
    
    def should_preempt(self, ready_queue: List[Process]) -> bool:
        """
        Determina si se debe hacer un cambio de contexto (preemption) con SRTF.
        Hace preemption si hay un proceso en la cola de listos con menor tiempo restante.
        
        Args:
            ready_queue: Cola de procesos listos
            
        Returns:
            True si se debe hacer preemption, False en caso contrario
        """
        if not self.current_process:
            return False
        
        # SRTF: Preemption si hay un proceso con menor tiempo restante
        if ready_queue:
            best_ready = min(ready_queue, key=lambda p: p.remaining_time)
            if best_ready.remaining_time < self.current_process.remaining_time:
                return True
        
        return False
    
    def start_execution(self, process: Process) -> None:
        """
        Inicia la ejecución de un proceso.
        
        Args:
            process: Proceso a ejecutar
        """
        self.current_process = process
        process.state = ProcessState.EXECUTING
    
    def execute_tick(self) -> Optional[Process]:
        """
        Ejecuta una unidad de tiempo del proceso actual.
        
        Returns:
            El proceso si terminó, None en caso contrario
        """
        if not self.current_process:
            return None
        
        self.current_process.remaining_time -= 1
        
        # Verificar si el proceso terminó
        if self.current_process.remaining_time <= 0:
            finished = self.current_process
            finished.state = ProcessState.TERMINATED
            self.current_process = None
            return finished
        
        return None
    
    def preempt_current(self) -> Optional[Process]:
        """
        Hace preemption del proceso actual.
        
        Returns:
            El proceso que fue preemptado
        """
        if not self.current_process:
            return None
        
        preempted = self.current_process
        preempted.state = ProcessState.READY
        self.current_process = None
        return preempted


# ============================================================================
# INTERFAZ DE USUARIO
# ============================================================================

class Display:
    """Maneja la visualización de información del simulador."""
    
    @staticmethod
    def clear_screen():
        """Limpia la pantalla."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def show_memory_table(partitions: List[Partition], os_size: int = 100):
        """
        Muestra la tabla de distribución de memoria.
        Según especificaciones: 100K para SO, luego particiones de 250K, 150K, 50K.
        
        Args:
            partitions: Lista de particiones
            os_size: Tamaño del sistema operativo (100K según especificaciones)
        """
        try:
            from tabulate import tabulate
            
            headers = ["Partición", "Tamaño", "Proceso", "Frag. Interna"]
            table_data = []
            
            # Sistema operativo
            table_data.append(["SO", f"{os_size}K", "SO", "---"])
            
            # Particiones
            for partition in partitions:
                process_id = partition.process.id if partition.process else "Libre"
                frag = f"{partition.internal_fragmentation}K" if partition.process else "---"
                table_data.append([
                    partition.id,
                    f"{partition.size}K",
                    process_id,
                    frag
                ])
            
            print("\n" + "="*60)
            print("DISTRIBUCIÓN DE MEMORIA")
            print("="*60)
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print("="*60 + "\n")
            
        except ImportError:
            # Fallback sin tabulate
            print("\n" + "="*60)
            print("DISTRIBUCIÓN DE MEMORIA")
            print("="*60)
            print(f"{'Partición':<12} {'Tamaño':<10} {'Proceso':<10} {'Frag. Interna':<15}")
            print("-"*60)
            print(f"{'SO':<12} {os_size:<10}K {'SO':<10} {'---':<15}")
            for partition in partitions:
                process_id = partition.process.id if partition.process else "Libre"
                frag = f"{partition.internal_fragmentation}K" if partition.process else "---"
                print(f"{partition.id:<12} {partition.size:<10}K {process_id:<10} {frag:<15}")
            print("="*60 + "\n")
    
    @staticmethod
    def show_process_queues(processes: List[Process], ready_queue: List[int], 
                           suspended_queue: List[int], executing_id: Optional[int],
                           clock: int = 0):
        """
        Muestra las colas de procesos.
        
        Args:
            processes: Lista de todos los procesos
            ready_queue: IDs de procesos en cola de listos
            suspended_queue: IDs de procesos suspendidos
            executing_id: ID del proceso en ejecución
            clock: Tiempo actual para filtrar procesos que aún no han llegado
        """
        try:
            from tabulate import tabulate
            
            # Organizar procesos por estado
            executing = []
            ready = []
            suspended = []
            new = []
            terminated = []
            
            # Usar un set para evitar duplicados
            seen_ids = set()
            
            for process in processes:
                # Evitar mostrar el mismo proceso dos veces
                if process.id in seen_ids:
                    continue
                seen_ids.add(process.id)
                
                if process.id == executing_id:
                    executing.append(process.id)
                elif process.state.value == "Ready":
                    # Si está en ready_queue o si no se especificó la lista, mostrarlo
                    if not ready_queue or process.id in ready_queue:
                        ready.append(process.id)
                elif process.state.value == "Suspended":
                    # Si está en suspended_queue o si no se especificó la lista, mostrarlo
                    if not suspended_queue or process.id in suspended_queue:
                        suspended.append(process.id)
                elif process.state.value == "New":
                    # Solo mostrar procesos que realmente están en estado New
                    # (excluir los que aún no han llegado: arrival_time > clock)
                    if process.arrival_time <= clock:
                        new.append(process.id)
                elif process.state.value == "Terminated":
                    # Solo mostrar procesos que realmente terminaron (remaining_time debe ser 0)
                    if process.remaining_time <= 0:
                        terminated.append(process.id)
            
            table_data = [
                ["Ejecución", ", ".join(map(str, executing)) if executing else "---"],
                ["Listo", ", ".join(map(str, ready)) if ready else "---"],
                ["Listo/Suspendido", ", ".join(map(str, suspended)) if suspended else "---"],
                ["Nuevo", ", ".join(map(str, new)) if new else "---"],
                ["Terminado", ", ".join(map(str, terminated)) if terminated else "---"],
            ]
            
            print("="*60)
            print("COLAS DE PROCESOS")
            print("="*60)
            print(tabulate(table_data, headers=["Estado", "Procesos"], tablefmt="grid"))
            print("="*60 + "\n")
            
        except ImportError:
            # Fallback sin tabulate
            print("="*60)
            print("COLAS DE PROCESOS")
            print("="*60)
            print(f"{'Estado':<20} {'Procesos':<40}")
            print("-"*60)
            # Similar lógica pero con print simple
            print("="*60 + "\n")
    
    @staticmethod
    def show_statistics(processes: List[Process], clock: int):
        """
        Muestra las estadísticas finales de la simulación.
        
        Args:
            processes: Lista de todos los procesos
            clock: Tiempo total de simulación
        """
        # Incluir todos los procesos que se cargaron (terminados o no)
        # Si un proceso no terminó, mostrar "N/A" en los campos correspondientes
        all_processes = sorted(processes, key=lambda p: p.id)
        terminated = [p for p in all_processes if p.state.value == "Terminated"]
        
        if not all_processes:
            print("\nNo hay procesos para mostrar estadísticas.")
            return
        
        try:
            from tabulate import tabulate
            
            headers = ["Proceso", "T. Arribo", "T. Irrupción", "T. Fin", "T. Retorno", "T. Espera"]
            table_data = []
            
            total_turnaround = 0
            total_wait = 0
            count_terminated = 0
            
            for process in all_processes:
                if process.state.value == "Terminated":
                    process.calculate_statistics()
                    table_data.append([
                        process.id,
                        process.arrival_time,
                        process.burst_time,
                        process.finish_time,
                        process.turnaround_time,
                        process.wait_time
                    ])
                    total_turnaround += process.turnaround_time
                    total_wait += process.wait_time
                    count_terminated += 1
                else:
                    # Proceso que no terminó (no cabe en memoria, etc.)
                    table_data.append([
                        process.id,
                        process.arrival_time,
                        process.burst_time,
                        "N/A",
                        "N/A",
                        process.wait_time  # Mostrar tiempo de espera acumulado
                    ])
            
            # Promedios solo de procesos terminados
            if count_terminated > 0:
                avg_turnaround = total_turnaround / count_terminated
                avg_wait = total_wait / count_terminated
            else:
                avg_turnaround = 0
                avg_wait = 0
            throughput = count_terminated / clock if clock > 0 else 0
            
            table_data.append(["PROMEDIOS", "---", "---", "---", 
                              f"{avg_turnaround:.2f}", f"{avg_wait:.2f}"])
            
            print("\n" + "="*80)
            print("INFORME ESTADÍSTICO")
            print("="*80)
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            print("="*80)
            print(f"Rendimiento del sistema: {throughput:.4f} procesos/unidad de tiempo")
            print("="*80 + "\n")
            
        except ImportError:
            # Fallback sin tabulate
            print("\n" + "="*80)
            print("INFORME ESTADÍSTICO")
            print("="*80)
            print(f"{'Proceso':<10} {'T. Arribo':<12} {'T. Irrupción':<15} "
                  f"{'T. Fin':<10} {'T. Retorno':<12} {'T. Espera':<12}")
            print("-"*80)
            for process in sorted(terminated, key=lambda p: p.id):
                process.calculate_statistics()
                print(f"{process.id:<10} {process.arrival_time:<12} {process.burst_time:<15} "
                      f"{process.finish_time:<10} {process.turnaround_time:<12} {process.wait_time:<12}")
            print("="*80 + "\n")
    
    @staticmethod
    def show_time(clock: int):
        """Muestra el tiempo actual de simulación."""
        print(f"\n{'='*60}")
        print(f"TIEMPO: {clock}")
        print(f"{'='*60}")
    
    @staticmethod
    def wait_for_continue():
        """Espera a que el usuario presione Enter."""
        input("\nPresione Enter para continuar...")


class Menu:
    """Maneja la interfaz de menú del simulador."""
    
    def __init__(self):
        """Inicializa el menú."""
        self.display = Display()
    
    def show_main_menu(self):
        """Muestra el menú principal."""
        self.display.clear_screen()
        print("="*60)
        print("SIMULADOR DE ASIGNACIÓN DE MEMORIA Y PLANIFICACIÓN")
        print("="*60)
        print("\n1. Cargar archivo de procesos")
        print("2. Salir")
        print("\n" + "="*60)
    
    def get_file_input(self) -> Optional[str]:
        """
        Solicita al usuario el nombre del archivo.
        
        Returns:
            Nombre del archivo o None si se cancela
        """
        print("\nIngrese el nombre del archivo CSV (o 'cancelar' para volver):")
        filename = input("> ").strip()
        
        if filename.lower() == 'cancelar':
            return None
        
        # Agregar extensión .csv si no la tiene
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        return filename
    
    def load_file(self) -> Optional[List[Process]]:
        """
        Carga un archivo de procesos.
        
        Returns:
            Lista de procesos o None si hubo error
        """
        filename = self.get_file_input()
        
        if filename is None:
            return None
        
        processes = FileReader.read_processes(filename)
        
        if processes:
            FileReader.preview_processes(processes)
            confirm = input("¿Confirmar carga? (s/n): ").strip().lower()
            
            if confirm == 's' or confirm == 'si' or confirm == 'sí':
                return processes
            else:
                print("Carga cancelada.")
                input("\nPresione Enter para continuar...")
                return None
        else:
            input("\nPresione Enter para continuar...")
            return None
    
    def show_simulation_options(self) -> dict:
        """
        Muestra opciones de configuración de simulación.
        
        Returns:
            Diccionario con las opciones seleccionadas
        """
        self.display.clear_screen()
        print("="*60)
        print("CONFIGURACIÓN DE SIMULACIÓN")
        print("="*60)
        
        # Algoritmo de planificación - Solo SRTF según especificaciones
        print("\nAlgoritmo de planificación: SRTF (Shortest Remaining Time First)")
        algorithm = 'SRTF'
        
        # Grado de multiprogramación
        dom_input = input("\nGrado de multiprogramación (default=5): ").strip()
        try:
            degree_of_multiprogramming = int(dom_input) if dom_input else 5
        except ValueError:
            degree_of_multiprogramming = 5
        
        # Particiones de memoria según especificaciones del TP
        print("\nConfiguración de particiones de memoria:")
        print("1. Configuración del TP (250K, 150K, 50K) - POR DEFECTO")
        print("2. Configuración alternativa (60K, 120K, 250K)")
        print("3. Personalizada")
        
        part_choice = input("\nSeleccione (1-3, default=1): ").strip()
        
        if part_choice == '2':
            partitions = [
                {'id': 1, 'size': 60, 'start': 100},
                {'id': 2, 'size': 120, 'start': 161},
                {'id': 3, 'size': 250, 'start': 281}
            ]
        elif part_choice == '3':
            partitions = []
            print("\nIngrese las particiones (formato: id,tamaño,dirección_inicio):")
            print("Ejemplo: 1,100,200")
            print("Escriba 'fin' para terminar")
            part_id = 1
            while True:
                part_input = input(f"Partición {part_id}: ").strip()
                if part_input.lower() == 'fin':
                    break
                try:
                    parts = part_input.split(',')
                    if len(parts) == 3:
                        partitions.append({
                            'id': int(parts[0]),
                            'size': int(parts[1]),
                            'start': int(parts[2])
                        })
                        part_id += 1
                except ValueError:
                    print("Formato inválido. Intente nuevamente.")
        else:
            # Configuración según especificaciones del TP:
            # 100K para SO (no se crea partición, es reservado)
            # 250K, 150K, 50K para procesos
            partitions = [
                {'id': 1, 'size': 250, 'start': 100},  # Trabajos grandes
                {'id': 2, 'size': 150, 'start': 350},  # Trabajos medianos
                {'id': 3, 'size': 50, 'start': 500}    # Trabajos pequeños
            ]
        
        return {
            'algorithm': algorithm,
            'degree_of_multiprogramming': degree_of_multiprogramming,
            'partitions': partitions
        }
    
    def wait_for_continue(self):
        """Espera a que el usuario presione Enter."""
        input("\nPresione Enter para continuar...")


# ============================================================================
# SIMULADOR
# ============================================================================

class Simulator:
    """Simulador principal del sistema operativo."""
    
    def __init__(self, partitions: List[Partition], 
                 degree_of_multiprogramming: int = 5):
        """
        Inicializa el simulador.
        
        Args:
            partitions: Lista de particiones de memoria
            degree_of_multiprogramming: Grado de multiprogramación (máximo de procesos en memoria)
        """
        self.partitions = partitions
        self.degree_of_multiprogramming = degree_of_multiprogramming
        self.clock = 0
        
        # Componentes del sistema
        self.memory_manager = MemoryManager(partitions)
        self.scheduler = Scheduler()  # Solo SRTF
        self.display = Display()
        
        # Colas de procesos
        self.all_processes: List[Process] = []  # Procesos que aún no han llegado
        self.loaded_processes: List[Process] = []  # Todos los procesos cargados (para estadísticas)
        self.new_queue: List[Process] = []
        self.ready_queue: List[Process] = []
        self.suspended_queue: List[Process] = []
        self.terminated_queue: List[Process] = []
        
        # Control de eventos para visualización
        self.new_process_arrived = False
        self.process_finished = False
    
    def load_processes(self, processes: List[Process]):
        """
        Carga los procesos en el simulador.
        
        Args:
            processes: Lista de procesos a simular
        """
        self.all_processes = processes.copy()
        self.loaded_processes = processes.copy()  # Guardar todos los procesos para estadísticas
        self.new_queue = []
        self.ready_queue = []
        self.suspended_queue = []
        self.terminated_queue = []
        self.clock = 0
    
    def _arrive_new_processes(self):
        """Maneja la llegada de nuevos procesos."""
        arrived = []
        remaining = []
        
        for process in self.all_processes:
            if process.arrival_time == self.clock:
                process.state = ProcessState.NEW
                arrived.append(process)
                self.new_process_arrived = True  # Marcar que llegó un nuevo proceso
            elif process.arrival_time > self.clock:
                remaining.append(process)
            # Los que ya llegaron se manejan en otras colas
        
        self.all_processes = remaining
        
        # Intentar cargar los nuevos procesos a memoria
        for process in arrived:
            self._try_load_to_memory(process)
    
    def _try_load_to_memory(self, process: Process):
        """
        Intenta cargar un proceso a memoria.
        
        Args:
            process: Proceso a cargar
        """
        # Verificar grado de multiprogramación
        current_dom = len(self.ready_queue) + (1 if self.scheduler.current_process else 0)
        
        if current_dom >= self.degree_of_multiprogramming:
            # No hay espacio, ir a suspendidos
            process.state = ProcessState.SUSPENDED
            if process not in self.suspended_queue:
                self.suspended_queue.append(process)
            return
        
        # Intentar asignar memoria
        if self.memory_manager.allocate_process(process):
            if process not in self.ready_queue:
                self.ready_queue.append(process)
            if process in self.suspended_queue:
                self.suspended_queue.remove(process)
        else:
            # No cabe en memoria, ir a suspendidos
            process.state = ProcessState.SUSPENDED
            if process not in self.suspended_queue:
                self.suspended_queue.append(process)
    
    def _try_load_suspended(self):
        """Intenta cargar procesos suspendidos a memoria."""
        current_dom = len(self.ready_queue) + (1 if self.scheduler.current_process else 0)
        
        if current_dom >= self.degree_of_multiprogramming:
            return
        
        # Intentar cargar suspendidos
        to_remove = []
        for process in self.suspended_queue:
            if current_dom >= self.degree_of_multiprogramming:
                break
            
            if self.memory_manager.allocate_process(process):
                if process not in self.ready_queue:
                    self.ready_queue.append(process)
                to_remove.append(process)
                current_dom += 1
        
        for process in to_remove:
            self.suspended_queue.remove(process)
    
    def _update_wait_times(self):
        """
        Actualiza los tiempos de espera de los procesos.
        Solo cuenta el tiempo para procesos que están esperando ANTES de ejecutarse por primera vez.
        Una vez que un proceso se ejecuta, ya no cuenta más tiempo de espera.
        """
        # Actualizar tiempo de espera solo para procesos que NO están ejecutándose
        # y que AÚN NO se han ejecutado por primera vez
        executing_id = self.scheduler.current_process.id if self.scheduler.current_process else None
        
        for process in self.ready_queue + self.suspended_queue:
            # Solo actualizar si:
            # 1. El proceso está esperando (READY o SUSPENDED)
            # 2. NO es el que está ejecutándose ahora
            # 3. AÚN NO se ha ejecutado por primera vez (first_execution_time es None)
            if (process.state == ProcessState.READY or process.state == ProcessState.SUSPENDED) and \
               process.id != executing_id and \
               process.first_execution_time is None:
                process.wait_time += 1
    
    def _schedule_process(self):
        """Planifica el siguiente proceso a ejecutar."""
        # Verificar si hay que hacer preemption
        if self.scheduler.should_preempt(self.ready_queue):
            preempted = self.scheduler.preempt_current()
            if preempted and preempted not in self.ready_queue:
                self.ready_queue.append(preempted)
        
        # Seleccionar siguiente proceso
        if not self.scheduler.current_process:
            next_process = self.scheduler.select_next_process(self.ready_queue)
            if next_process:
                # Marcar la primera vez que se ejecuta (para calcular tiempo de espera)
                if next_process.first_execution_time is None:
                    next_process.first_execution_time = self.clock
                self.scheduler.start_execution(next_process)
                if next_process in self.ready_queue:
                    self.ready_queue.remove(next_process)
    
    def _execute_tick(self):
        """Ejecuta una unidad de tiempo."""
        finished = self.scheduler.execute_tick()
        
        if finished:
            # Validar que el proceso realmente terminó
            if finished.remaining_time <= 0 and finished.state == ProcessState.TERMINATED:
                # Proceso terminado
                # finish_time es el tiempo al final del tick actual (clock + 1)
                finished.finish_time = self.clock + 1
                finished.calculate_statistics()
                self.memory_manager.free_process(finished)
                # Solo agregar si no está ya en la cola
                if finished not in self.terminated_queue:
                    self.terminated_queue.append(finished)
                self.scheduler.current_process = None
                self.process_finished = True  # Marcar que terminó un proceso
    
    def run(self):
        """
        Ejecuta la simulación.
        Muestra salida cada vez que llega un nuevo proceso o termina uno en ejecución.
        No permite corridas ininterrumpidas.
        """
        print("\n" + "="*60)
        print("INICIANDO SIMULACIÓN")
        print("="*60)
        print("Algoritmo: SRTF (Shortest Remaining Time First)")
        print("="*60)
        
        # Contar procesos totales
        total_processes = len(self.all_processes)
        
        # Bucle principal
        max_ticks = 1000  # Límite de seguridad
        while len(self.terminated_queue) < total_processes:
            
            if self.clock >= max_ticks:
                print(f"\nAdvertencia: Simulación detenida por límite de tiempo ({max_ticks} ticks).")
                break
            
            # Resetear flags de eventos
            self.new_process_arrived = False
            self.process_finished = False
            
            # 1. Llegada de nuevos procesos
            self._arrive_new_processes()
            
            # 2. Intentar cargar suspendidos a memoria
            self._try_load_suspended()
            
            # 3. Planificar proceso (ANTES de actualizar tiempos de espera)
            self._schedule_process()
            
            # 4. Actualizar tiempos de espera (solo para procesos que NO están ejecutándose)
            # Esto se hace DESPUÉS de planificar para no contar el tiempo si se ejecuta
            self._update_wait_times()
            
            # 5. Ejecutar tick
            self._execute_tick()
            
            # 6. Mostrar estado si llegó un nuevo proceso o terminó uno
            if self.new_process_arrived or self.process_finished:
                self.display.show_time(self.clock)
                self.display.show_memory_table(self.partitions)
                # Construir lista completa de procesos activos
                # Incluir todos los procesos que ya llegaron (no los que están en all_processes esperando llegar)
                # Usar listas separadas para evitar duplicados
                all_active_processes = []
                seen_ids = set()
                
                # Agregar proceso en ejecución (si hay uno)
                if self.scheduler.current_process:
                    if self.scheduler.current_process.id not in seen_ids:
                        all_active_processes.append(self.scheduler.current_process)
                        seen_ids.add(self.scheduler.current_process.id)
                
                # Agregar procesos de ready_queue
                for p in self.ready_queue:
                    if p.id not in seen_ids:
                        all_active_processes.append(p)
                        seen_ids.add(p.id)
                
                # Agregar procesos de suspended_queue
                for p in self.suspended_queue:
                    if p.id not in seen_ids:
                        all_active_processes.append(p)
                        seen_ids.add(p.id)
                
                # Agregar procesos terminados (solo los que realmente terminaron)
                for p in self.terminated_queue:
                    if p.id not in seen_ids and p.state == ProcessState.TERMINATED:
                        all_active_processes.append(p)
                        seen_ids.add(p.id)
                self.display.show_process_queues(
                    all_active_processes,
                    [p.id for p in self.ready_queue],
                    [p.id for p in self.suspended_queue],
                    self.scheduler.current_process.id if self.scheduler.current_process else None,
                    self.clock
                )
                self.display.wait_for_continue()
            
            # 7. Avanzar reloj
            self.clock += 1
        
        # Mostrar estado final
        self.display.show_time(self.clock)
        self.display.show_memory_table(self.partitions)
        all_processes_list = self.ready_queue + self.suspended_queue + self.terminated_queue
        self.display.show_process_queues(
            all_processes_list,
            [p.id for p in self.ready_queue],
            [p.id for p in self.suspended_queue],
            self.scheduler.current_process.id if self.scheduler.current_process else None,
            self.clock
        )
        
        # Mostrar estadísticas finales
        print("\n" + "="*60)
        print("SIMULACIÓN FINALIZADA")
        print("="*60)
        # Pasar todos los procesos cargados para estadísticas (no solo los activos)
        self.display.show_statistics(self.loaded_processes, self.clock)


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Función principal del programa."""
    menu = Menu()
    
    while True:
        menu.show_main_menu()
        choice = input("Seleccione una opción: ").strip()
        
        if choice == '1':
            # Cargar archivo
            processes = menu.load_file()
            
            if processes:
                # Configurar simulación
                config = menu.show_simulation_options()
                
                # Crear particiones
                partitions = []
                for part_config in config['partitions']:
                    partitions.append(Partition(
                        id=part_config['id'],
                        size=part_config['size'],
                        start_address=part_config['start']
                    ))
                
                # Crear y ejecutar simulador (solo SRTF según especificaciones)
                simulator = Simulator(
                    partitions=partitions,
                    degree_of_multiprogramming=config['degree_of_multiprogramming']
                )
                
                simulator.load_processes(processes)
                
                # Ejecutar simulación (siempre muestra cuando llega proceso nuevo o termina uno)
                simulator.run()
                
                input("\nPresione Enter para volver al menú principal...")
        
        elif choice == '2':
            print("\n¡Hasta luego!")
            break
        
        else:
            print("\nOpción inválida. Por favor seleccione 1 o 2.")
            input("Presione Enter para continuar...")


if __name__ == "__main__":
    main()

