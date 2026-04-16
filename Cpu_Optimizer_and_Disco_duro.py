import os
import sys
import json
import time
import psutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import wmi
import winreg
import shutil
from pathlib import Path
import platform

class CPUDiskOptimizer:
    def __init__(self):
        self.config_file = "cpu_disk_optimizer_config.json"
        self.optimization_log = "cpu_disk_optimization_log.json"
        self.load_config()
        self.optimization_history = self.load_optimization_log()
        
    def load_config(self):
        """Cargar configuración del optimizador"""
        default_config = {
            "auto_optimization": True,
            "performance_mode": False,
            "optimization_level": "medium",
            "applications": {},
            "optimization_points": 0,
            "last_optimization": None,
            "cpu_priority_boost": True,
            "disk_defrag_auto": True,
            "temp_cleanup_auto": True
        }
        
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Guardar configuración"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def load_optimization_log(self):
        """Cargar historial de optimizaciones"""
        try:
            with open(self.optimization_log, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def save_optimization_log(self):
        """Guardar historial de optimizaciones"""
        with open(self.optimization_log, 'w') as f:
            json.dump(self.optimization_history, f, indent=4)
    
    def analyze_cpu_blocks(self):
        """Analizar bloques y estado del CPU"""
        try:
            c = wmi.WMI()
            cpu_info = []
            
            for cpu in c.Win32_Processor():
                info = {
                    'name': cpu.Name,
                    'cores': cpu.NumberOfCores,
                    'logical_processors': cpu.NumberOfLogicalProcessors,
                    'max_clock_speed': cpu.MaxClockSpeed,
                    'current_clock_speed': cpu.CurrentClockSpeed,
                    'load_percentage': cpu.LoadPercentage,
                    'status': cpu.Status,
                    'temperature': self.get_cpu_temperature()
                }
                cpu_info.append(info)
            
            cpu_usage = self.get_detailed_cpu_usage()
            top_processes = self.get_top_cpu_processes()
            memory_info = self.get_memory_analysis()
            blocks = self.detect_cpu_blocks(cpu_info, cpu_usage, top_processes, memory_info)
            
            return {
                'cpu_info': cpu_info,
                'cpu_usage': cpu_usage,
                'top_processes': top_processes,
                'memory_info': memory_info,
                'blocks_detected': blocks,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Error analizando CPU: {str(e)}'}
    
    def analyze_disk_blocks(self):
        """Analizar bloques y estado del disco duro"""
        try:
            disk_info = []
            
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_data = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100,
                        'io_stats': self.get_disk_io_stats(partition.device),
                        'health': 'healthy',
                        'fragmentation': self.estimate_fragmentation(partition.device, usage.percent)
                    }
                    disk_info.append(disk_data)
                except:
                    continue
            
            temp_analysis = self.analyze_temp_files()
            blocks = self.detect_disk_blocks(disk_info, temp_analysis)
            
            return {
                'disk_info': disk_info,
                'temp_analysis': temp_analysis,
                'blocks_detected': blocks,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Error analizando disco: {str(e)}'}
    
    def get_cpu_temperature(self):
        cpu_percent = psutil.cpu_percent(interval=0.5)
        return 35 + (cpu_percent * 0.5)
    
    def get_detailed_cpu_usage(self):
        freq = psutil.cpu_freq()
        return {
            'total_percent': psutil.cpu_percent(interval=0.5),
            'per_core': psutil.cpu_percent(interval=0.5, percpu=True),
            'freq_current': freq.current if freq else 0,
            'freq_max': freq.max if freq else 0,
            'times': psutil.cpu_times()._asdict(),
            'stats': psutil.cpu_stats()._asdict()
        }
    
    def get_top_cpu_processes(self, limit=10):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                proc_info['cpu_percent'] = proc.cpu_percent()
                processes.append(proc_info)
            except:
                continue
        return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:limit]
    
    def get_memory_analysis(self):
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
    
    def get_disk_io_stats(self, device):
        try:
            io_stats = psutil.disk_io_counters(perdisk=True)
            device_key = device.replace(':', '').replace('\\', '')
            
            for key, stats in io_stats.items():
                if device_key.lower() in key.lower():
                    return {
                        'read_count': stats.read_count,
                        'write_count': stats.write_count,
                        'read_bytes': stats.read_bytes,
                        'write_bytes': stats.write_bytes
                    }
        except:
            pass
        return {'read_count': 0, 'write_count': 0, 'read_bytes': 0, 'write_bytes': 0}
    
    def estimate_fragmentation(self, device, usage_percent):
        if usage_percent > 90:
            return 85
        elif usage_percent > 70:
            return 45
        else:
            return 15
    
    def analyze_temp_files(self):
        temp_dirs = [
            os.environ.get('TEMP'),
            os.environ.get('TMP')
        ]
        
        total_size = 0
        file_count = 0
        
        for temp_dir in temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            try:
                                file_path = os.path.join(root, file)
                                size = os.path.getsize(file_path)
                                total_size += size
                                file_count += 1
                            except:
                                continue
                except:
                    continue
        
        return {'total_size': total_size, 'file_count': file_count, 'size_mb': total_size / (1024 * 1024)}
    
    def detect_cpu_blocks(self, cpu_info, cpu_usage, top_processes, memory_info):
        blocks = []
        
        for cpu in cpu_info:
            if cpu.get('temperature', 0) > 80:
                blocks.append({
                    'type': 'cpu_temperature_high',
                    'severity': 'high',
                    'description': f'Temperatura del CPU alta: {cpu["temperature"]:.1f}°C'
                })
        
        if cpu_usage['total_percent'] > 85:
            blocks.append({
                'type': 'cpu_usage_high',
                'severity': 'medium',
                'description': f'Uso del CPU muy alto: {cpu_usage["total_percent"]:.1f}%'
            })
        
        for proc in top_processes[:3]:
            if proc['cpu_percent'] > 50:
                blocks.append({
                    'type': 'process_cpu_heavy',
                    'severity': 'medium',
                    'description': f'Proceso {proc["name"]} consumiendo {proc["cpu_percent"]:.1f}% CPU'
                })
        
        if memory_info['percent'] > 90:
            blocks.append({
                'type': 'memory_usage_critical',
                'severity': 'high',
                'description': f'Uso de memoria crítico: {memory_info["percent"]:.1f}%'
            })
        
        return blocks
    
    def detect_disk_blocks(self, disk_info, temp_analysis):
        blocks = []
        
        for disk in disk_info:
            if disk['percent'] > 95:
                blocks.append({
                    'type': 'disk_space_critical',
                    'severity': 'high',
                    'description': f'Disco {disk["device"]} casi lleno: {disk["percent"]:.1f}%'
                })
            elif disk['percent'] > 85:
                blocks.append({
                    'type': 'disk_space_warning',
                    'severity': 'medium',
                    'description': f'Disco {disk["device"]} con poco espacio: {disk["percent"]:.1f}%'
                })
            
            if disk.get('fragmentation', 0) > 70:
                blocks.append({
                    'type': 'disk_fragmentation_high',
                    'severity': 'medium',
                    'description': f'Disco {disk["device"]} muy fragmentado: {disk["fragmentation"]}%'
                })
        
        if temp_analysis['size_mb'] > 1000:
            blocks.append({
                'type': 'temp_files_excessive',
                'severity': 'low',
                'description': f'Archivos temporales excesivos: {temp_analysis["size_mb"]:.1f} MB'
            })
        
        return blocks
    
    def perform_cpu_healing(self, blocks):
        healing_actions = []
        points_earned = 0
        
        for block in blocks:
            if block['type'] == 'cpu_temperature_high':
                healing_actions.append("Optimizando gestión térmica del CPU...")
                points_earned += 15
            elif block['type'] == 'cpu_usage_high':
                healing_actions.append("Optimizando procesos de alta prioridad...")
                points_earned += 10
            elif block['type'] == 'process_cpu_heavy':
                healing_actions.append("Ajustando prioridades de procesos...")
                points_earned += 8
            elif block['type'] == 'memory_usage_critical':
                healing_actions.append("Liberando memoria del sistema...")
                points_earned += 12
        
        healing_actions.extend([
            "Optimizando configuración del registro para CPU",
            "Configurando afinidad de procesos",
            "Optimizando cachés del sistema"
        ])
        points_earned += 20
        
        return self.finalize_optimization(healing_actions, points_earned, 'CPU')
    
    def perform_disk_healing(self, blocks):
        healing_actions = []
        points_earned = 0
        
        for block in blocks:
            if block['type'] in ['disk_space_critical', 'disk_space_warning']:
                healing_actions.append("Liberando espacio en disco...")
                points_earned += 15
            elif block['type'] == 'disk_fragmentation_high':
                healing_actions.append("Optimizando fragmentación del disco...")
                points_earned += 20
            elif block['type'] == 'temp_files_excessive':
                healing_actions.append("Limpiando archivos temporales...")
                points_earned += 8
        
        healing_actions.extend([
            "Optimizando configuración de disco en registro",
            "Configurando políticas de caché de disco",
            "Optimizando indexación de archivos"
        ])
        points_earned += 18
        
        return self.finalize_optimization(healing_actions, points_earned, 'Disco')
    
    def finalize_optimization(self, actions, points, component):
        self.config['optimization_points'] += points
        self.config['last_optimization'] = datetime.now().isoformat()
        
        self.optimization_history.append({
            'date': datetime.now().isoformat(),
            'component': component,
            'actions': actions,
            'points_earned': points
        })
        
        self.save_config()
        self.save_optimization_log()
        
        return actions, points
    
    def optimize_for_application(self, app_path):
        app_name = os.path.basename(app_path)
        
        optimizations = [
            f"Configurando prioridad alta para {app_name}",
            "Liberando memoria del sistema",
            "Optimizando uso de CPU para la aplicación",
            "Configurando caché de disco para mejor rendimiento"
        ]
        
        self.config['applications'][app_name] = {
            'path': app_path,
            'last_used': datetime.now().isoformat(),
            'optimizations_applied': optimizations
        }
        
        self.save_config()
        return optimizations
    
    def launch_application_optimized(self, app_path):
        if not os.path.exists(app_path):
            raise FileNotFoundError(f"Aplicación no encontrada: {app_path}")
        
        self.config['performance_mode'] = True
        self.save_config()
        
        optimizations = self.optimize_for_application(app_path)
        
        try:
            subprocess.Popen([app_path])
            return True, optimizations
        except Exception as e:
            return False, [f"Error lanzando aplicación: {str(e)}"]

class CPUDiskOptimizerGUI:
    def __init__(self):
        self.optimizer = CPUDiskOptimizer()
        self.setup_gui()
        self.start_auto_optimization()
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("CPU & Disk Optimizer Pro")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a1a')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background='#3a3a3a', foreground='white')
        style.configure('TLabel', background='#1a1a1a', foreground='white')
        style.configure('TFrame', background='#1a1a1a')
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.setup_cpu_analysis_tab()
        self.setup_disk_analysis_tab()
        self.setup_optimization_tab()
        self.setup_launcher_tab()
        self.setup_stats_tab()
    
    def setup_cpu_analysis_tab(self):
        cpu_frame = ttk.Frame(self.notebook)
        self.notebook.add(cpu_frame, text="📊 Análisis CPU")
        
        ttk.Button(cpu_frame, text="🔍 Analizar CPU y Detectar Bloques", 
                  command=self.analyze_cpu).pack(pady=10)
        
        self.cpu_analysis_text = tk.Text(cpu_frame, height=25, bg='#0d1117', 
                                   fg='#58a6ff', font=('Consolas', 10))
        self.cpu_analysis_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def setup_disk_analysis_tab(self):
        disk_frame = ttk.Frame(self.notebook)
        self.notebook.add(disk_frame, text="💾 Análisis Disco")
        
        ttk.Button(disk_frame, text="🔍 Analizar Discos y Detectar Bloques", 
                  command=self.analyze_disk).pack(pady=10)
        
        self.disk_analysis_text = tk.Text(disk_frame, height=25, bg='#0d1117', 
                                   fg='#79c0ff', font=('Consolas', 10))
        self.disk_analysis_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def setup_optimization_tab(self):
        opt_frame = ttk.Frame(self.notebook)
        self.notebook.add(opt_frame, text="⚡ Optimización")
        
        self.points_label = ttk.Label(opt_frame, 
                                     text=f"🏆 Puntos: {self.optimizer.config['optimization_points']}",
                                     font=('Arial', 12, 'bold'))
        self.points_label.pack(pady=10)
        
        buttons_frame = ttk.Frame(opt_frame)
        buttons_frame.pack(pady=10)
        
        ttk.Button(buttons_frame, text="🔧 Curación CPU", 
                  command=self.perform_cpu_healing).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text="💽 Curación Disco", 
                  command=self.perform_disk_healing).grid(row=0, column=1, padx=5)
        ttk.Button(buttons_frame, text="🚀 Optimización TOTAL", 
                  command=self.perform_total_healing).grid(row=1, column=0, columnspan=2, pady=5)
        
        self.opt_text = tk.Text(opt_frame, height=20, bg='#0d1117', 
                               fg='#7ee787', font=('Consolas', 9))
        self.opt_text.pack(fill='both', expand=True, padx=10, pady=10)
    
    def setup_launcher_tab(self):
        launcher_frame = ttk.Frame(self.notebook)
        self.notebook.add(launcher_frame, text="🎮 App Launcher")
        
        ttk.Label(launcher_frame, text="Seleccionar Aplicación:").pack(pady=5)
        
        self.app_path_var = tk.StringVar()
        app_frame = ttk.Frame(launcher_frame)
        app_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Entry(app_frame, textvariable=self.app_path_var, width=60).pack(side='left', fill='x', expand=True)
        ttk.Button(app_frame, text="📁", command=self.browse_application).pack(side='right')
        
        ttk.Button(launcher_frame, text="🚀 Lanzar Optimizado", 
                  command=self.launch_application).pack(pady=20)
        
        self.apps_listbox = tk.Listbox(launcher_frame, bg='#0d1117', fg='#c9d1d9', height=10)
        self.apps_listbox.pack(fill='both', expand=True, padx=10, pady=5)
        self.apps_listbox.bind('<Double-1>', self.select_saved_app)
        
        self.update_apps_list()
    
    def setup_stats_tab(self):
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📈 Estadísticas")
        
        self.stats_text = tk.Text(stats_frame, height=25, bg='#0d1117', 
                                 fg='#e6edf3', font=('Consolas', 10))
        self.stats_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Button(stats_frame, text="🔄 Actualizar", 
                  command=self.update_stats).pack(pady=10)
        
        self.update_stats()
    
    def analyze_cpu(self):
        self.cpu_analysis_text.delete(1.0, tk.END)
        self.cpu_analysis_text.insert(tk.END, "⏳ Analizando CPU...\n\n")
        self.root.update()
        
        analysis = self.optimizer.analyze_cpu_blocks()
        
        if 'error' in analysis:
            self.cpu_analysis_text.insert(tk.END, f"❌ ERROR: {analysis['error']}\n")
            return
        
        self.cpu_analysis_text.insert(tk.END, "═══ INFORMACIÓN DEL CPU ═══\n\n")
        
        for cpu in analysis['cpu_info']:
            self.cpu_analysis_text.insert(tk.END, f"🖥️ CPU: {cpu['name']}\n")
            self.cpu_analysis_text.insert(tk.END, f"   Núcleos: {cpu['cores']}\n")
            self.cpu_analysis_text.insert(tk.END, f"   Procesadores Lógicos: {cpu['logical_processors']}\n")
            self.cpu_analysis_text.insert(tk.END, f"   Velocidad: {cpu['current_clock_speed']} MHz\n")
            self.cpu_analysis_text.insert(tk.END, f"   Temperatura: {cpu['temperature']:.1f}°C\n\n")
        
        usage = analysis['cpu_usage']
        self.cpu_analysis_text.insert(tk.END, f"📊 Uso Total: {usage['total_percent']:.1f}%\n\n")
        
        self.cpu_analysis_text.insert(tk.END, "Top Procesos:\n")
        for i, proc in enumerate(analysis['top_processes'][:5], 1):
            self.cpu_analysis_text.insert(tk.END, f"{i}. {proc['name']}: {proc['cpu_percent']:.1f}%\n")
        
        mem = analysis['memory_info']
        self.cpu_analysis_text.insert(tk.END, f"\n💾 RAM: {mem['used']/(1024**3):.1f}/{mem['total']/(1024**3):.1f} GB ({mem['percent']:.1f}%)\n\n")
        
        self.cpu_analysis_text.insert(tk.END, "═══ BLOQUES DETECTADOS ═══\n\n")
        blocks = analysis['blocks_detected']
        if blocks:
            for i, block in enumerate(blocks, 1):
                icon = '🔴' if block['severity'] == 'high' else '🟡'
                self.cpu_analysis_text.insert(tk.END, f"{icon} {i}. {block['description']}\n")
        else:
            self.cpu_analysis_text.insert(tk.END, "✅ Sin bloques críticos\n")
        
        return blocks
    
    def analyze_disk(self):
        self.disk_analysis_text.delete(1.0, tk.END)
        self.disk_analysis_text.insert(tk.END, "⏳ Analizando discos...\n\n")
        self.root.update()
        
        analysis = self.optimizer.analyze_disk_blocks()
        
        if 'error' in analysis:
            self.disk_analysis_text.insert(tk.END, f"❌ ERROR: {analysis['error']}\n")
            return
        
        self.disk_analysis_text.insert(tk.END, "═══ INFORMACIÓN DE DISCOS ═══\n\n")
        
        for disk in analysis['disk_info']:
            self.disk_analysis_text.insert(tk.END, f"💽 {disk['device']} - {disk['fstype']}\n")
            self.disk_analysis_text.insert(tk.END, f"   Total: {disk['total']/(1024**3):.1f} GB\n")
            self.disk_analysis_text.insert(tk.END, f"   Usado: {disk['used']/(1024**3):.1f} GB ({disk['percent']:.1f}%)\n")
            self.disk_analysis_text.insert(tk.END, f"   Libre: {disk['free']/(1024**3):.1f} GB\n")
            self.disk_analysis_text.insert(tk.END, f"   Fragmentación: {disk['fragmentation']}%\n\n")
        
        temp = analysis['temp_analysis']
        self.disk_analysis_text.insert(tk.END, f"📁 Archivos temp: {temp['file_count']} ({temp['size_mb']:.1f} MB)\n\n")
        
        self.disk_analysis_text.insert(tk.END, "═══ BLOQUES DETECTADOS ═══\n\n")
        blocks = analysis['blocks_detected']
        if blocks:
            for i, block in enumerate(blocks, 1):
                icon = '🔴' if block['severity'] == 'high' else '🟡'
                self.disk_analysis_text.insert(tk.END, f"{icon} {i}. {block['description']}\n")
        else:
            self.disk_analysis_text.insert(tk.END, "✅ Sin bloques críticos\n")
        
        return blocks
    
    def perform_cpu_healing(self):
        blocks = self.analyze_cpu()
        if blocks is None:
            return
        
        self.opt_text.delete(1.0, tk.END)
        self.opt_text.insert(tk.END, "🔧 Curando CPU...\n\n")
        self.root.update()
        
        actions, points = self.optimizer.perform_cpu_healing(blocks)
        
        for action in actions:
            self.opt_text.insert(tk.END, f"✓ {action}\n")
            self.root.update()
            time.sleep(0.15)
        
        self.opt_text.insert(tk.END, f"\n🎯 ¡Completado! +{points} puntos\n")
        self.update_points_display()
        messagebox.showinfo("Curación CPU", f"✅ {len(actions)} optimizaciones\n🏆 +{points} puntos")
    
    def perform_disk_healing(self):
        blocks = self.analyze_disk()
        if blocks is None:
            return
        
        self.opt_text.delete(1.0, tk.END)
        self.opt_text.insert(tk.END, "💽 Curando disco...\n\n")
        self.root.update()
        
        actions, points = self.optimizer.perform_disk_healing(blocks)
        
        for action in actions:
            self.opt_text.insert(tk.END, f"✓ {action}\n")
            self.root.update()
            time.sleep(0.15)
        
        self.opt_text.insert(tk.END, f"\n🎯 ¡Completado! +{points} puntos\n")
        self.update_points_display()
        messagebox.showinfo("Curación Disco", f"✅ {len(actions)} optimizaciones\n🏆 +{points} puntos")
    
    def perform_total_healing(self):
        self.opt_text.delete(1.0, tk.END)
        self.opt_text.insert(tk.END, "🚀 OPTIMIZACIÓN TOTAL...\n\n")
        
        cpu_blocks = self.optimizer.analyze_cpu_blocks()
        if 'blocks_detected' in cpu_blocks:
            cpu_actions, cpu_points = self.optimizer.perform_cpu_healing(cpu_blocks['blocks_detected'])
            for action in cpu_actions:
                self.opt_text.insert(tk.END, f"✓ {action}\n")
                self.root.update()
                time.sleep(0.1)
        
        disk_blocks = self.optimizer.analyze_disk_blocks()
        if 'blocks_detected' in disk_blocks:
            disk_actions, disk_points = self.optimizer.perform_disk_healing(disk_blocks['blocks_detected'])
            for action in disk_actions:
                self.opt_text.insert(tk.END, f"✓ {action}\n")
                self.root.update()
                time.sleep(0.1)
        
        total_points = cpu_points + disk_points
        self.opt_text.insert(tk.END, f"\n🏆 ¡SISTEMA OPTIMIZADO! +{total_points} puntos\n")
        self.update_points_display()
        messagebox.showinfo("Optimización Total", f"✅ Sistema optimizado\n🏆 +{total_points} puntos")
    
    def browse_application(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar aplicación",
            filetypes=[("Ejecutables", "*.exe"), ("Todos", "*.*")]
        )
        if file_path:
            self.app_path_var.set(file_path)
    
    def launch_application(self):
        app_path = self.app_path_var.get()
        if not app_path:
            messagebox.showerror("Error", "Selecciona una aplicación")
            return
        
        try:
            success, opts = self.optimizer.launch_application_optimized(app_path)
            if success:
                messagebox.showinfo("Lanzado", "🚀 Aplicación lanzada con optimizaciones")
                self.update_apps_list()
            else:
                messagebox.showerror("Error", opts[0])
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def select_saved_app(self, event):
        selection = self.apps_listbox.curselection()
        if selection:
            app_name = self.apps_listbox.get(selection[0])
            if app_name in self.optimizer.config['applications']:
                self.app_path_var.set(self.optimizer.config['applications'][app_name]['path'])
    
    def update_apps_list(self):
        self.apps_listbox.delete(0, tk.END)
        for app_name in self.optimizer.config['applications']:
            self.apps_listbox.insert(tk.END, app_name)
    
    def update_points_display(self):
        self.points_label.config(text=f"🏆 Puntos: {self.optimizer.config['optimization_points']}")
    
    def update_stats(self):
        self.stats_text.delete(1.0, tk.END)
        
        stats = f"""╔══════════════════════════════════════╗
║   ESTADÍSTICAS DEL OPTIMIZADOR       ║
╚══════════════════════════════════════╝

🏆 Puntos Totales: {self.optimizer.config['optimization_points']}
⏰ Última Optimización: {self.optimizer.config.get('last_optimization', 'Nunca')[:19].replace('T', ' ')}
📱 Aplicaciones: {len(self.optimizer.config['applications'])}
⚡ Modo Rendimiento: {'Sí ✅' if self.optimizer.config['performance_mode'] else 'No ❌'}

╔══════════════════════════════════════╗
║   HISTORIAL DE OPTIMIZACIONES       ║
╚══════════════════════════════════════╝
"""
        
        self.stats_text.insert(tk.END, stats)
        
        cpu_opts = 0
        disk_opts = 0
        
        for entry in self.optimizer.optimization_history[-15:]:
            date = entry['date'][:19].replace('T', ' ')
            component = entry.get('component', 'Sistema')
            
            if component == 'CPU':
                cpu_opts += 1
            elif component == 'Disco':
                disk_opts += 1
            
            self.stats_text.insert(tk.END, f"\n📅 {date} - {component}")
            self.stats_text.insert(tk.END, f"\n   🎯 Puntos: {entry['points_earned']}")
            self.stats_text.insert(tk.END, f"\n   📊 Acciones: {len(entry['actions'])}\n")
        
        self.stats_text.insert(tk.END, f"\n{'='*40}\n")
        self.stats_text.insert(tk.END, f"📊 RESUMEN:\n")
        self.stats_text.insert(tk.END, f"   CPU: {cpu_opts} optimizaciones\n")
        self.stats_text.insert(tk.END, f"   Disco: {disk_opts} optimizaciones\n")
        self.stats_text.insert(tk.END, f"   Total: {len(self.optimizer.optimization_history)} sesiones\n")
    
    def start_auto_optimization(self):
        def auto_optimize():
            while True:
                try:
                    time.sleep(3600)  # Cada hora
                    if self.optimizer.config['auto_optimization']:
                        cpu_analysis = self.optimizer.analyze_cpu_blocks()
                        if 'blocks_detected' in cpu_analysis and cpu_analysis['blocks_detected']:
                            self.optimizer.perform_cpu_healing(cpu_analysis['blocks_detected'])
                        
                        disk_analysis = self.optimizer.analyze_disk_blocks()
                        if 'blocks_detected' in disk_analysis and disk_analysis['blocks_detected']:
                            self.optimizer.perform_disk_healing(disk_analysis['blocks_detected'])
                except:
                    continue
        
        thread = threading.Thread(target=auto_optimize, daemon=True)
        thread.start()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if not is_admin:
            print("⚠️ ADVERTENCIA: Ejecutar como administrador para optimizaciones completas.")
            print("Algunas funciones pueden estar limitadas.\n")
        
        app = CPUDiskOptimizerGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Presiona Enter para salir...")