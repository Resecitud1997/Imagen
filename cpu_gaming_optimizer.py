import psutil
import threading
import time
import json
import os
import subprocess
import winreg
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

@dataclass
class CPUBlock:
    """Representa un 'bloque' de CPU similar a núcleos de GPU"""
    core_id: int
    usage_percent: float
    frequency: float
    temperature: Optional[float]
    load_history: List[float]
    efficiency_score: float
    
class CPUAnalyzer:
    """Analizador de CPU que trata cada núcleo como un bloque procesador"""
    
    def __init__(self):
        self.cpu_blocks = {}
        self.monitoring = False
        self.optimization_data = self.load_optimization_data()
        self.daily_cure_points = 0
        self.total_cure_points = self.optimization_data.get('total_cure_points', 0)
        
    def load_optimization_data(self) -> Dict:
        """Carga datos de optimización guardados"""
        try:
            if os.path.exists('cpu_optimization.json'):
                with open('cpu_optimization.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            'total_cure_points': 0,
            'optimization_history': [],
            'game_profiles': {},
            'last_cure_date': None
        }
    
    def save_optimization_data(self):
        """Guarda datos de optimización"""
        self.optimization_data['total_cure_points'] = self.total_cure_points
        self.optimization_data['last_cure_date'] = datetime.now().isoformat()
        with open('cpu_optimization.json', 'w') as f:
            json.dump(self.optimization_data, f, indent=2)
    
    def analyze_cpu_blocks(self) -> Dict[int, CPUBlock]:
        """Analiza cada núcleo CPU como un bloque procesador"""
        cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq_per_core = psutil.cpu_freq(percpu=True)
        
        blocks = {}
        for i, (usage, freq_info) in enumerate(zip(cpu_percent_per_core, cpu_freq_per_core)):
            # Calcular eficiencia del bloque
            efficiency = self.calculate_block_efficiency(usage, freq_info.current if freq_info else 0)
            
            # Mantener historial de carga
            if i in self.cpu_blocks:
                history = self.cpu_blocks[i].load_history[-20:]  # Últimos 20 valores
                history.append(usage)
            else:
                history = [usage]
            
            blocks[i] = CPUBlock(
                core_id=i,
                usage_percent=usage,
                frequency=freq_info.current if freq_info else 0,
                temperature=None,  # Requiere librerías adicionales como openhardwaremonitor
                load_history=history,
                efficiency_score=efficiency
            )
        
        self.cpu_blocks = blocks
        return blocks
    
    def calculate_block_efficiency(self, usage: float, frequency: float) -> float:
        """Calcula la eficiencia de un bloque CPU"""
        if frequency == 0:
            return 0
        # Eficiencia = trabajo útil / recursos consumidos
        return (usage * frequency) / (100 * frequency) * 100
    
    def perform_cpu_cure(self) -> int:
        """Realiza 'curación' del CPU optimizando configuraciones"""
        cure_points = 0
        
        # 1. Optimizar procesos en segundo plano
        cure_points += self.optimize_background_processes()
        
        # 2. Ajustar prioridades de sistema
        cure_points += self.optimize_system_priorities()
        
        # 3. Limpiar memoria y cache
        cure_points += self.optimize_memory()
        
        # 4. Configurar plan de energía
        cure_points += self.optimize_power_plan()
        
        self.daily_cure_points += cure_points
        self.total_cure_points += cure_points
        
        # Guardar progreso
        self.optimization_data['optimization_history'].append({
            'date': datetime.now().isoformat(),
            'cure_points': cure_points,
            'total_points': self.total_cure_points
        })
        
        self.save_optimization_data()
        return cure_points
    
    def optimize_background_processes(self) -> int:
        """Optimiza procesos en segundo plano"""
        cure_points = 0
        
        # Lista de procesos que suelen consumir recursos innecesarios
        processes_to_optimize = [
            'Windows Search', 'Cortana', 'OneDrive',
            'Windows Update', 'Telemetry', 'Defender'
        ]
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if any(opt_proc.lower() in proc.info['name'].lower() 
                       for opt_proc in processes_to_optimize):
                    if proc.info['cpu_percent'] > 5:  # Si consume más del 5%
                        # Reducir prioridad
                        process = psutil.Process(proc.info['pid'])
                        if process.nice() != psutil.BELOW_NORMAL_PRIORITY_CLASS:
                            process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                            cure_points += 2
            except:
                continue
        
        return cure_points
    
    def optimize_system_priorities(self) -> int:
        """Optimiza prioridades del sistema para gaming"""
        cure_points = 0
        
        try:
            # Configurar sistema para priorizar programas sobre servicios
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SYSTEM\CurrentControlSet\Control\PriorityControl", 
                               0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "Win32PrioritySeparation", 0, winreg.REG_DWORD, 38)
            winreg.CloseKey(key)
            cure_points += 5
            
            # Desactivar throttling del procesador
            subprocess.run(['powercfg', '/setacvalueindex', 'scheme_current', 
                          'sub_processor', 'PROCTHROTTLEMIN', '100'], 
                         capture_output=True, check=False)
            cure_points += 3
            
        except Exception as e:
            print(f"Error optimizando prioridades: {e}")
        
        return cure_points
    
    def optimize_memory(self) -> int:
        """Optimiza uso de memoria"""
        cure_points = 0
        
        try:
            # Limpiar archivos temporales
            temp_dirs = [os.environ.get('TEMP'), os.environ.get('TMP')]
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        try:
                            file_path = os.path.join(temp_dir, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                cure_points += 0.1
                        except:
                            continue
            
            # Ejecutar limpieza de memoria
            subprocess.run(['sfc', '/scannow'], capture_output=True, check=False)
            cure_points += 10
            
        except Exception as e:
            print(f"Error optimizando memoria: {e}")
        
        return int(cure_points)
    
    def optimize_power_plan(self) -> int:
        """Configura plan de energía para máximo rendimiento"""
        cure_points = 0
        
        try:
            # Activar plan de alto rendimiento
            result = subprocess.run(['powercfg', '/setactive', 
                                   '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                cure_points += 15
            
            # Configurar procesador al 100%
            subprocess.run(['powercfg', '/setacvalueindex', 'scheme_current', 
                          'sub_processor', 'PROCTHROTTLEMAX', '100'], 
                         capture_output=True, check=False)
            cure_points += 5
            
        except Exception as e:
            print(f"Error configurando plan de energía: {e}")
        
        return cure_points

class GameOptimizer:
    """Optimizador específico para videojuegos"""
    
    def __init__(self, cpu_analyzer: CPUAnalyzer):
        self.cpu_analyzer = cpu_analyzer
        self.game_profiles = {}
        self.load_game_profiles()
    
    def load_game_profiles(self):
        """Carga perfiles de juegos guardados"""
        self.game_profiles = self.cpu_analyzer.optimization_data.get('game_profiles', {})
    
    def create_game_profile(self, game_name: str, game_exe: str, 
                          priority: str = "High", affinity_cores: List[int] = None):
        """Crea un perfil específico para un juego"""
        profile = {
            'name': game_name,
            'executable': game_exe,
            'priority': priority,
            'affinity_cores': affinity_cores or list(range(psutil.cpu_count())),
            'optimizations': {
                'disable_fullscreen_opt': True,
                'disable_game_mode': False,
                'gpu_preference': 'high_performance',
                'memory_priority': 'high'
            }
        }
        
        self.game_profiles[game_name] = profile
        self.cpu_analyzer.optimization_data['game_profiles'] = self.game_profiles
        self.cpu_analyzer.save_optimization_data()
        
        return profile
    
    def optimize_for_game(self, game_name: str) -> bool:
        """Optimiza el sistema para un juego específico"""
        if game_name not in self.game_profiles:
            return False
        
        profile = self.game_profiles[game_name]
        
        try:
            # Encontrar proceso del juego
            game_process = None
            for proc in psutil.process_iter(['pid', 'name']):
                if profile['executable'].lower() in proc.info['name'].lower():
                    game_process = psutil.Process(proc.info['pid'])
                    break
            
            if game_process:
                # Establecer alta prioridad
                if profile['priority'] == 'High':
                    game_process.nice(psutil.HIGH_PRIORITY_CLASS)
                elif profile['priority'] == 'RealTime':
                    game_process.nice(psutil.REALTIME_PRIORITY_CLASS)
                
                # Configurar afinidad de CPU
                if profile['affinity_cores']:
                    game_process.cpu_affinity(profile['affinity_cores'])
                
                return True
                
        except Exception as e:
            print(f"Error optimizando juego {game_name}: {e}")
        
        return False
    
    def launch_game_optimized(self, game_path: str, game_name: str = None):
        """Lanza un juego con optimizaciones aplicadas"""
        if not game_name:
            game_name = os.path.basename(game_path)
        
        # Aplicar optimizaciones previas al lanzamiento
        self.cpu_analyzer.perform_cpu_cure()
        
        # Lanzar juego
        try:
            process = subprocess.Popen(game_path)
            
            # Esperar un momento para que el proceso se inicialice
            time.sleep(3)
            
            # Aplicar optimizaciones específicas del juego
            self.optimize_for_game(game_name)
            
            return process
            
        except Exception as e:
            print(f"Error lanzando juego: {e}")
            return None

class CPUOptimizerGUI:
    """Interfaz gráfica para el optimizador de CPU"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CPU Gaming Optimizer - Curación Diaria")
        self.root.geometry("1000x700")
        
        self.cpu_analyzer = CPUAnalyzer()
        self.game_optimizer = GameOptimizer(self.cpu_analyzer)
        
        self.setup_gui()
        self.monitoring = False
        
    def setup_gui(self):
        """Configura la interfaz gráfica"""
        # Notebook para pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña de análisis CPU
        self.setup_cpu_analysis_tab(notebook)
        
        # Pestaña de optimización
        self.setup_optimization_tab(notebook)
        
        # Pestaña de launcher de juegos
        self.setup_game_launcher_tab(notebook)
        
        # Pestaña de estadísticas
        self.setup_stats_tab(notebook)
    
    def setup_cpu_analysis_tab(self, notebook):
        """Configura pestaña de análisis de CPU"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Análisis CPU")
        
        # Botones de control
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Iniciar Monitoreo", 
                  command=self.start_monitoring).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Detener", 
                  command=self.stop_monitoring).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Curar CPU", 
                  command=self.perform_cure).pack(side='left', padx=5)
        
        # Información de puntos de curación
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill='x', padx=5, pady=5)
        
        self.cure_points_label = ttk.Label(info_frame, 
                                          text=f"Puntos de Curación Totales: {self.cpu_analyzer.total_cure_points}")
        self.cure_points_label.pack(side='left')
        
        self.daily_points_label = ttk.Label(info_frame, 
                                           text=f"Puntos Diarios: {self.cpu_analyzer.daily_cure_points}")
        self.daily_points_label.pack(side='right')
        
        # Gráfico de bloques CPU
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        # Tabla de información de bloques
        columns = ('Bloque', 'Uso %', 'Frecuencia', 'Eficiencia', 'Estado')
        self.cpu_tree = ttk.Treeview(frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.cpu_tree.heading(col, text=col)
            self.cpu_tree.column(col, width=100)
        
        self.cpu_tree.pack(fill='x', padx=5, pady=5)
    
    def setup_optimization_tab(self, notebook):
        """Configura pestaña de optimización"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Optimización")
        
        # Configuraciones de optimización
        ttk.Label(frame, text="Configuraciones de Optimización", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Checkboxes para diferentes optimizaciones
        self.opt_vars = {}
        optimizations = [
            ('Optimizar procesos en segundo plano', 'background_proc'),
            ('Configurar prioridades de sistema', 'system_priorities'),
            ('Limpiar memoria y caché', 'memory_clean'),
            ('Optimizar plan de energía', 'power_plan'),
            ('Desactivar servicios innecesarios', 'disable_services'),
            ('Optimizar registro de Windows', 'registry_opt')
        ]
        
        for text, key in optimizations:
            var = tk.BooleanVar(value=True)
            self.opt_vars[key] = var
            ttk.Checkbutton(frame, text=text, variable=var).pack(anchor='w', padx=20, pady=2)
        
        # Botón de optimización completa
        ttk.Button(frame, text="Ejecutar Optimización Completa", 
                  command=self.run_full_optimization).pack(pady=20)
        
        # Log de optimización
        ttk.Label(frame, text="Log de Optimización:").pack(anchor='w', padx=20)
        self.opt_log = tk.Text(frame, height=15, width=80)
        self.opt_log.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Scrollbar para el log
        scrollbar = ttk.Scrollbar(self.opt_log)
        scrollbar.pack(side='right', fill='y')
        self.opt_log.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.opt_log.yview)
    
    def setup_game_launcher_tab(self, notebook):
        """Configura pestaña del launcher de juegos"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Game Launcher")
        
        # Sección de perfiles de juegos
        profile_frame = ttk.LabelFrame(frame, text="Perfiles de Juegos")
        profile_frame.pack(fill='x', padx=10, pady=5)
        
        # Lista de juegos
        self.game_listbox = tk.Listbox(profile_frame, height=8)
        self.game_listbox.pack(fill='x', padx=5, pady=5)
        
        # Botones de gestión de juegos
        btn_frame = ttk.Frame(profile_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Agregar Juego", 
                  command=self.add_game_profile).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Lanzar Optimizado", 
                  command=self.launch_selected_game).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Eliminar", 
                  command=self.remove_game_profile).pack(side='left', padx=5)
        
        # Configuración del juego seleccionado
        config_frame = ttk.LabelFrame(frame, text="Configuración del Juego")
        config_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Prioridad del proceso
        ttk.Label(config_frame, text="Prioridad:").pack(anchor='w', padx=5)
        self.priority_var = tk.StringVar(value="High")
        priority_combo = ttk.Combobox(config_frame, textvariable=self.priority_var,
                                     values=["Normal", "High", "RealTime"])
        priority_combo.pack(fill='x', padx=5, pady=2)
        
        # Núcleos de CPU asignados
        ttk.Label(config_frame, text="Núcleos CPU asignados:").pack(anchor='w', padx=5)
        self.cores_frame = ttk.Frame(config_frame)
        self.cores_frame.pack(fill='x', padx=5, pady=2)
        
        self.core_vars = []
        for i in range(psutil.cpu_count()):
            var = tk.BooleanVar(value=True)
            self.core_vars.append(var)
            ttk.Checkbutton(self.cores_frame, text=f"Core {i}", variable=var).pack(side='left')
        
        # Cargar perfiles existentes
        self.refresh_game_list()
    
    def setup_stats_tab(self, notebook):
        """Configura pestaña de estadísticas"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Estadísticas")
        
        # Estadísticas generales
        stats_frame = ttk.LabelFrame(frame, text="Estadísticas de Curación")
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=10, width=80)
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Botón para actualizar estadísticas
        ttk.Button(stats_frame, text="Actualizar Estadísticas", 
                  command=self.update_statistics).pack(pady=5)
        
        # Gráfico de progreso
        self.stats_fig, self.stats_ax = plt.subplots(figsize=(10, 4))
        self.stats_canvas = FigureCanvasTkAgg(self.stats_fig, frame)
        self.stats_canvas.get_tk_widget().pack(fill='both', expand=True, padx=5, pady=5)
        
        self.update_statistics()
    
    def start_monitoring(self):
        """Inicia el monitoreo de CPU"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self.monitor_cpu)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.monitoring = False
    
    def monitor_cpu(self):
        """Hilo de monitoreo de CPU"""
        while self.monitoring:
            blocks = self.cpu_analyzer.analyze_cpu_blocks()
            self.update_cpu_display(blocks)
            time.sleep(1)
    
    def update_cpu_display(self, blocks: Dict[int, CPUBlock]):
        """Actualiza la visualización de bloques CPU"""
        # Limpiar tabla
        for item in self.cpu_tree.get_children():
            self.cpu_tree.delete(item)
        
        # Actualizar tabla
        for block_id, block in blocks.items():
            status = "Óptimo" if block.efficiency_score > 70 else "Necesita curación"
            self.cpu_tree.insert('', 'end', values=(
                f"Bloque {block_id}",
                f"{block.usage_percent:.1f}%",
                f"{block.frequency:.0f} MHz",
                f"{block.efficiency_score:.1f}%",
                status
            ))
        
        # Actualizar gráfico
        self.ax.clear()
        block_ids = list(blocks.keys())
        usages = [blocks[i].usage_percent for i in block_ids]
        colors = ['red' if usage > 80 else 'yellow' if usage > 50 else 'green' 
                 for usage in usages]
        
        self.ax.bar(block_ids, usages, color=colors, alpha=0.7)
        self.ax.set_xlabel('Bloque CPU')
        self.ax.set_ylabel('Uso (%)')
        self.ax.set_title('Estado de Bloques CPU')
        self.ax.set_ylim(0, 100)
        
        self.canvas.draw()
    
    def perform_cure(self):
        """Ejecuta curación de CPU"""
        cure_points = self.cpu_analyzer.perform_cpu_cure()
        
        # Actualizar labels
        self.cure_points_label.config(
            text=f"Puntos de Curación Totales: {self.cpu_analyzer.total_cure_points}")
        self.daily_points_label.config(
            text=f"Puntos Diarios: {self.cpu_analyzer.daily_cure_points}")
        
        messagebox.showinfo("Curación Completada", 
                           f"CPU curado exitosamente!\nPuntos obtenidos: {cure_points}")
    
    def run_full_optimization(self):
        """Ejecuta optimización completa según configuración"""
        self.opt_log.delete(1.0, tk.END)
        self.opt_log.insert(tk.END, f"=== Iniciando optimización completa - {datetime.now()} ===\n")
        
        total_points = 0
        
        if self.opt_vars['background_proc'].get():
            points = self.cpu_analyzer.optimize_background_processes()
            total_points += points
            self.opt_log.insert(tk.END, f"✓ Procesos optimizados: +{points} puntos\n")
        
        if self.opt_vars['system_priorities'].get():
            points = self.cpu_analyzer.optimize_system_priorities()
            total_points += points
            self.opt_log.insert(tk.END, f"✓ Prioridades configuradas: +{points} puntos\n")
        
        if self.opt_vars['memory_clean'].get():
            points = self.cpu_analyzer.optimize_memory()
            total_points += points
            self.opt_log.insert(tk.END, f"✓ Memoria optimizada: +{points} puntos\n")
        
        if self.opt_vars['power_plan'].get():
            points = self.cpu_analyzer.optimize_power_plan()
            total_points += points
            self.opt_log.insert(tk.END, f"✓ Plan de energía configurado: +{points} puntos\n")
        
        self.cpu_analyzer.total_cure_points += total_points
        self.cpu_analyzer.daily_cure_points += total_points
        self.cpu_analyzer.save_optimization_data()
        
        self.opt_log.insert(tk.END, f"\n=== Optimización completada: +{total_points} puntos totales ===\n")
        self.opt_log.see(tk.END)
        
        # Actualizar labels principales
        self.cure_points_label.config(
            text=f"Puntos de Curación Totales: {self.cpu_analyzer.total_cure_points}")
        self.daily_points_label.config(
            text=f"Puntos Diarios: {self.cpu_analyzer.daily_cure_points}")
    
    def add_game_profile(self):
        """Añade un nuevo perfil de juego"""
        game_path = filedialog.askopenfilename(
            title="Seleccionar ejecutable del juego",
            filetypes=[("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")]
        )
        
        if game_path:
            game_name = os.path.splitext(os.path.basename(game_path))[0]
            
            # Obtener núcleos seleccionados
            selected_cores = [i for i, var in enumerate(self.core_vars) if var.get()]
            
            # Crear perfil
            self.game_optimizer.create_game_profile(
                game_name=game_name,
                game_exe=os.path.basename(game_path),
                priority=self.priority_var.get(),
                affinity_cores=selected_cores
            )
            
            self.refresh_game_list()
            messagebox.showinfo("Perfil Creado", f"Perfil para {game_name} creado exitosamente!")
    
    def refresh_game_list(self):
        """Actualiza la lista de juegos"""
        self.game_listbox.delete(0, tk.END)
        for game_name in self.game_optimizer.game_profiles.keys():
            self.game_listbox.insert(tk.END, game_name)
    
    def launch_selected_game(self):
        """Lanza el juego seleccionado con optimizaciones"""
        selection = self.game_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un juego primero")
            return
        
        game_name = self.game_listbox.get(selection[0])
        
        # Solicitar ruta del ejecutable
        game_path = filedialog.askopenfilename(
            title=f"Seleccionar ejecutable de {game_name}",
            filetypes=[("Ejecutables", "*.exe"), ("Todos los archivos", "*.*")]
        )
        
        if game_path:
            # Realizar curación previa
            cure_points = self.cpu_analyzer.perform_cpu_cure()
            
            # Lanzar juego optimizado
            process = self.game_optimizer.launch_game_optimized(game_path, game_name)
            
            if process:
                messagebox.showinfo("Juego Lanzado", 
                                   f"{game_name} lanzado con optimizaciones!\n"
                                   f"Curación previa: +{cure_points} puntos")
            else:
                messagebox.showerror("Error", f"No se pudo lanzar {game_name}")
    
    def remove_game_profile(self):
        """Elimina un perfil de juego"""
        selection = self.game_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un juego primero")
            return
        
        game_name = self.game_listbox.get(selection[0])
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar perfil de {game_name}?"):
            del self.game_optimizer.game_profiles[game_name]
            self.cpu_analyzer.optimization_data['game_profiles'] = self.game_optimizer.game_profiles
            self.cpu_analyzer.save_optimization_data()
            self.refresh_game_list()
            messagebox.showinfo("Perfil Eliminado", f"Perfil de {game_name} eliminado")
    
    def update_statistics(self):
        """Actualiza las estadísticas de curación"""
        stats_text = f"""
=== ESTADÍSTICAS DE CURACIÓN CPU ===

Puntos Totales de Curación: {self.cpu_analyzer.total_cure_points}
Puntos Diarios: {self.cpu_analyzer.daily_cure_points}
Fecha Última Curación: {self.cpu_analyzer.optimization_data.get('last_cure_date', 'Nunca')}

=== INFORMACIÓN DEL SISTEMA ===
CPU: {psutil.cpu_count()} núcleos lógicos
RAM Total: {psutil.virtual_memory().total // (1024**3)} GB
RAM Disponible: {psutil.virtual_memory().available // (1024**3)} GB
Uso CPU Actual: {psutil.cpu_percent()}%

=== HISTORIAL DE OPTIMIZACIONES ===
"""
        
        history = self.cpu_analyzer.optimization_data.get('optimization_history', [])
        for entry in history[-10:]:  # Últimas 10 entradas
            date = datetime.fromisoformat(entry['date']).strftime('%Y-%m-%d %H:%M')
            stats_text += f"{date}: +{entry['cure_points']} puntos (Total: {entry['total_points']})\n"
        
        if not history:
            stats_text += "No hay historial de optimizaciones aún.\n"
        
        stats_text += f"\n=== PERFILES DE JUEGOS ===\n"
        for game_name, profile in self.game_optimizer.game_profiles.items():
            stats_text += f"• {game_name} - Prioridad: {profile['priority']}, "
            stats_text += f"Núcleos: {len(profile['affinity_cores'])}\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        
        # Actualizar gráfico de progreso
        self.update_progress_chart()
    
    def update_progress_chart(self):
        """Actualiza el gráfico de progreso de curación"""
        self.stats_ax.clear()
        
        history = self.cpu_analyzer.optimization_data.get('optimization_history', [])
        if history:
            dates = [datetime.fromisoformat(entry['date']) for entry in history[-30:]]
            points = [entry['total_points'] for entry in history[-30:]]
            
            self.stats_ax.plot(dates, points, marker='o', linewidth=2, markersize=4)
            self.stats_ax.set_title('Progreso de Puntos de Curación (Últimos 30 días)')
            self.stats_ax.set_xlabel('Fecha')
            self.stats_ax.set_ylabel('Puntos Totales')
            self.stats_ax.grid(True, alpha=0.3)
            
            # Rotar etiquetas de fecha
            self.stats_fig.autofmt_xdate()
        else:
            self.stats_ax.text(0.5, 0.5, 'No hay datos de historial aún', 
                              ha='center', va='center', transform=self.stats_ax.transAxes)
        
        self.stats_canvas.draw()
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

class AdvancedCPUOptimizer:
    """Optimizador avanzado con funciones adicionales"""
    
    def __init__(self, cpu_analyzer: CPUAnalyzer):
        self.cpu_analyzer = cpu_analyzer
        self.thermal_monitoring = False
        self.performance_profiles = {
            'gaming': {
                'cpu_priority': 'high',
                'memory_management': 'aggressive',
                'background_apps': 'minimal',
                'power_plan': 'ultimate_performance'
            },
            'streaming': {
                'cpu_priority': 'balanced',
                'memory_management': 'moderate',
                'background_apps': 'selective',
                'power_plan': 'high_performance'
            },
            'productivity': {
                'cpu_priority': 'normal',
                'memory_management': 'conservative',
                'background_apps': 'normal',
                'power_plan': 'balanced'
            }
        }
    
    def enable_game_mode(self):
        """Activa modo gaming extremo"""
        try:
            # Configurar Windows Game Mode
            subprocess.run(['reg', 'add', 
                          'HKCU\\SOFTWARE\\Microsoft\\GameBar', 
                          '/v', 'AllowAutoGameMode', '/t', 'REG_DWORD', 
                          '/d', '1', '/f'], check=False)
            
            # Desactivar Windows Update durante gaming
            subprocess.run(['sc', 'config', 'wuauserv', 'start=', 'disabled'], check=False)
            
            # Configurar TCP/IP para gaming
            subprocess.run(['netsh', 'int', 'tcp', 'set', 'global', 
                          'autotuninglevel=normal'], check=False)
            
            # Configurar GPU para máximo rendimiento
            subprocess.run(['powercfg', '/setacvalueindex', 'scheme_current', 
                          'sub_graphics', 'GPUPOWERPREFS', '2'], check=False)
            
            return True
        except Exception as e:
            print(f"Error activando modo gaming: {e}")
            return False
    
    def optimize_network_for_gaming(self):
        """Optimiza configuración de red para gaming"""
        try:
            # Configurar buffer de red
            subprocess.run(['netsh', 'int', 'tcp', 'set', 'global', 
                          'chimney=enabled'], check=False)
            
            # Optimizar ventana TCP
            subprocess.run(['netsh', 'int', 'tcp', 'set', 'global', 
                          'autotuninglevel=normal'], check=False)
            
            # Configurar RSS (Receive Side Scaling)
            subprocess.run(['netsh', 'int', 'tcp', 'set', 'global', 
                          'rss=enabled'], check=False)
            
            return True
        except Exception as e:
            print(f"Error optimizando red: {e}")
            return False
    
    def create_restore_point(self):
        """Crea punto de restauración del sistema"""
        try:
            subprocess.run(['powershell', '-Command', 
                          'Checkpoint-Computer -Description "CPU_Optimizer_Backup"'], 
                         check=False)
            return True
        except Exception as e:
            print(f"Error creando punto de restauración: {e}")
            return False
    
    def monitor_temperatures(self):
        """Monitorea temperaturas del sistema (requiere sensores)"""
        try:
            # Nota: Esto requiere WMI o librerías adicionales
            # Por ahora simulamos con datos de CPU
            import wmi
            w = wmi.WMI(namespace="root\\wmi")
            temperature_info = w.MSAcpi_ThermalZoneStatus()
            
            temps = []
            for temp in temperature_info:
                if temp.CurrentTemperature:
                    # Convertir de décimas de Kelvin a Celsius
                    celsius = (temp.CurrentTemperature / 10.0) - 273.15
                    temps.append(celsius)
            
            return temps
        except:
            # Simulación de temperaturas
            return [45.0, 42.0, 48.0, 44.0]  # Temperaturas simuladas
    
    def apply_performance_profile(self, profile_name: str):
        """Aplica un perfil de rendimiento específico"""
        if profile_name not in self.performance_profiles:
            return False
        
        profile = self.performance_profiles[profile_name]
        cure_points = 0
        
        try:
            # Aplicar configuraciones según el perfil
            if profile['power_plan'] == 'ultimate_performance':
                subprocess.run(['powercfg', '/setactive', 
                              'e9a42b02-d5df-448d-aa00-03f14749eb61'], check=False)
                cure_points += 20
            elif profile['power_plan'] == 'high_performance':
                subprocess.run(['powercfg', '/setactive', 
                              '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'], check=False)
                cure_points += 15
            
            # Gestión de memoria según perfil
            if profile['memory_management'] == 'aggressive':
                self.aggressive_memory_management()
                cure_points += 10
            
            # Gestión de aplicaciones en segundo plano
            if profile['background_apps'] == 'minimal':
                self.minimize_background_apps()
                cure_points += 15
            
            self.cpu_analyzer.total_cure_points += cure_points
            return True
            
        except Exception as e:
            print(f"Error aplicando perfil {profile_name}: {e}")
            return False
    
    def aggressive_memory_management(self):
        """Gestión agresiva de memoria para gaming"""
        try:
            # Configurar memoria virtual
            subprocess.run(['wmic', 'computersystem', 'where', 
                          'name="%computername%"', 'set', 
                          'AutomaticManagedPagefile=False'], check=False)
            
            # Limpiar caché de DNS
            subprocess.run(['ipconfig', '/flushdns'], check=False)
            
            # Limpiar archivos temporales de forma agresiva
            import shutil
            temp_dirs = [
                os.environ.get('TEMP'),
                os.environ.get('TMP'),
                os.path.join(os.environ.get('WINDIR', ''), 'Temp'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp')
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        os.makedirs(temp_dir, exist_ok=True)
                    except:
                        continue
            
        except Exception as e:
            print(f"Error en gestión agresiva de memoria: {e}")
    
    def minimize_background_apps(self):
        """Minimiza aplicaciones en segundo plano"""
        try:
            # Lista de procesos a minimizar/cerrar
            unnecessary_processes = [
                'skype.exe', 'spotify.exe', 'discord.exe', 'chrome.exe',
                'firefox.exe', 'steam.exe', 'origin.exe', 'uplay.exe',
                'epicgameslauncher.exe', 'battle.net.exe'
            ]
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    process_name = proc.info['name'].lower()
                    if any(unwanted in process_name for unwanted in unnecessary_processes):
                        # Minimizar en lugar de cerrar
                        process = psutil.Process(proc.info['pid'])
                        process.suspend()  # Suspender proceso
                        time.sleep(0.1)
                        process.resume()   # Reanudar para evitar crashes
                        process.nice(psutil.IDLE_PRIORITY_CLASS)  # Baja prioridad
                except:
                    continue
                    
        except Exception as e:
            print(f"Error minimizando aplicaciones: {e}")

# Funciones adicionales para el launcher
class GameLauncher:
    """Launcher especializado para videojuegos"""
    
    def __init__(self, cpu_analyzer: CPUAnalyzer, game_optimizer: GameOptimizer):
        self.cpu_analyzer = cpu_analyzer
        self.game_optimizer = game_optimizer
        self.advanced_optimizer = AdvancedCPUOptimizer(cpu_analyzer)
        self.running_games = {}
    
    def pre_launch_optimization(self, intensity: str = 'high'):
        """Optimización previa al lanzamiento del juego"""
        total_cure_points = 0
        
        # Crear punto de restauración
        if self.advanced_optimizer.create_restore_point():
            total_cure_points += 5
        
        # Aplicar perfil de gaming
        if self.advanced_optimizer.apply_performance_profile('gaming'):
            total_cure_points += 25
        
        # Activar modo gaming
        if self.advanced_optimizer.enable_game_mode():
            total_cure_points += 15
        
        # Optimizar red
        if self.advanced_optimizer.optimize_network_for_gaming():
            total_cure_points += 10
        
        # Curación estándar de CPU
        standard_cure = self.cpu_analyzer.perform_cpu_cure()
        total_cure_points += standard_cure
        
        return total_cure_points
    
    def launch_with_monitoring(self, game_path: str, game_name: str = None):
        """Lanza juego con monitoreo continuo"""
        if not game_name:
            game_name = os.path.basename(game_path)
        
        # Optimización previa
        cure_points = self.pre_launch_optimization()
        
        try:
            # Lanzar juego
            process = subprocess.Popen(game_path)
            self.running_games[game_name] = {
                'process': process,
                'start_time': datetime.now(),
                'cure_points': cure_points
            }
            
            # Iniciar monitoreo en hilo separado
            monitor_thread = threading.Thread(
                target=self.monitor_game_performance, 
                args=(game_name, process.pid)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return process, cure_points
            
        except Exception as e:
            print(f"Error lanzando {game_name}: {e}")
            return None, 0
    
    def monitor_game_performance(self, game_name: str, pid: int):
        """Monitorea el rendimiento durante el juego"""
        try:
            game_process = psutil.Process(pid)
            
            while game_process.is_running():
                # Monitorear uso de CPU del juego
                cpu_usage = game_process.cpu_percent()
                memory_usage = game_process.memory_percent()
                
                # Si el uso es bajo, aplicar micro-optimizaciones
                if cpu_usage < 30:  # El juego no está usando suficiente CPU
                    self.apply_micro_optimizations(game_process)
                
                # Monitorear temperaturas
                temps = self.advanced_optimizer.monitor_temperatures()
                if max(temps) > 80:  # Temperatura alta
                    self.apply_thermal_throttling_prevention()
                
                time.sleep(5)  # Revisar cada 5 segundos
                
        except psutil.NoSuchProcess:
            # El juego se cerró
            if game_name in self.running_games:
                del self.running_games[game_name]
        except Exception as e:
            print(f"Error monitoreando {game_name}: {e}")
    
    def apply_micro_optimizations(self, game_process):
        """Aplica micro-optimizaciones durante el juego"""
        try:
            # Aumentar ligeramente la prioridad si es necesario
            if game_process.nice() < psutil.HIGH_PRIORITY_CLASS:
                game_process.nice(psutil.HIGH_PRIORITY_CLASS)
            
            # Optimizar afinidad de CPU dinámicamente
            current_affinity = game_process.cpu_affinity()
            if len(current_affinity) < psutil.cpu_count():
                # Asignar más núcleos si están disponibles
                available_cores = list(range(psutil.cpu_count()))
                game_process.cpu_affinity(available_cores)
            
        except Exception as e:
            print(f"Error aplicando micro-optimizaciones: {e}")
    
    def apply_thermal_throttling_prevention(self):
        """Previene throttling térmico"""
        try:
            # Reducir frecuencia máxima temporalmente
            subprocess.run(['powercfg', '/setacvalueindex', 'scheme_current', 
                          'sub_processor', 'PROCTHROTTLEMAX', '90'], check=False)
            
            # Esperar 30 segundos y restaurar
            time.sleep(30)
            subprocess.run(['powercfg', '/setacvalueindex', 'scheme_current', 
                          'sub_processor', 'PROCTHROTTLEMAX', '100'], check=False)
            
        except Exception as e:
            print(f"Error previniendo throttling: {e}")

# Función principal para ejecutar la aplicación
def main():
    """Función principal"""
    try:
        app = CPUOptimizerGUI()
        app.run()
    except Exception as e:
        print(f"Error ejecutando la aplicación: {e}")
        messagebox.showerror("Error", f"Error crítico: {e}")

if __name__ == "__main__":
    # Verificar si se ejecuta como administrador (requerido para algunas optimizaciones)
    import ctypes
    
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    if not is_admin():
        print("ADVERTENCIA: Algunas optimizaciones requieren permisos de administrador.")
        print("Para obtener máxima efectividad, ejecuta como administrador.")
    
    # Ejecutar aplicación
    main()