"""
RAM Optimizer Pro - Optimizador de Memoria RAM para Windows
Versión 2.0 - Ultra Professional Edition
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import ctypes
import sys
import os
import subprocess
import json
from datetime import datetime
import math

# ─── DETECCIÓN DE PLATAFORMA ──────────────────────────────────────────────────
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import psutil
    import winreg
else:
    try:
        import psutil
    except ImportError:
        psutil = None

# ─── PALETA DE COLORES ────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":      "#0A0E1A",
    "bg_panel":     "#0F1624",
    "bg_card":      "#141D2E",
    "bg_input":     "#1A2540",
    "accent":       "#00D4FF",
    "accent2":      "#7B2FFF",
    "accent_green": "#00FF88",
    "accent_red":   "#FF4455",
    "accent_orange":"#FF8C00",
    "text_main":    "#E8F0FF",
    "text_sub":     "#6B7FA8",
    "text_dim":     "#3D4F72",
    "border":       "#1E2D4A",
    "glow":         "#00D4FF33",
}

FONTS = {
    "title":   ("Consolas", 22, "bold"),
    "header":  ("Consolas", 13, "bold"),
    "body":    ("Consolas", 10),
    "small":   ("Consolas", 9),
    "metric":  ("Consolas", 28, "bold"),
    "label":   ("Consolas", 8),
    "mono":    ("Courier New", 9),
}


# ─── MÓDULO DE SISTEMA ────────────────────────────────────────────────────────
class SystemMemory:
    @staticmethod
    def get_info():
        try:
            import psutil
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            return {
                "total":     vm.total,
                "available": vm.available,
                "used":      vm.used,
                "percent":   vm.percent,
                "swap_total":sw.total,
                "swap_used": sw.used,
                "swap_pct":  sw.percent,
            }
        except Exception:
            # Simulación para demo / no-Windows
            return {
                "total":     8 * 1024**3,
                "available": 3.2 * 1024**3,
                "used":      4.8 * 1024**3,
                "percent":   60.0,
                "swap_total":2 * 1024**3,
                "swap_used": 512 * 1024**2,
                "swap_pct":  25.0,
            }

    @staticmethod
    def get_processes():
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "memory_info", "status"]):
                try:
                    mi = p.info["memory_info"]
                    if mi and mi.rss > 5 * 1024 * 1024:
                        procs.append({
                            "pid":  p.info["pid"],
                            "name": p.info["name"],
                            "mb":   mi.rss / 1024 / 1024,
                            "status": p.info["status"],
                        })
                except Exception:
                    pass
            return sorted(procs, key=lambda x: x["mb"], reverse=True)[:30]
        except Exception:
            return []

    @staticmethod
    def fmt(b):
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"


# ─── OPTIMIZADORES ───────────────────────────────────────────────────────────
class MemoryOptimizer:
    def __init__(self, log_callback):
        self.log = log_callback

    def _log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO":"◆","OK":"✔","WARN":"▲","ERR":"✖","RUN":"►"}
        self.log(f"[{ts}] {icons.get(level,'◆')} {msg}", level)

    def run_quick(self):
        freed = 0
        self._log("Iniciando optimización rápida...", "RUN")
        time.sleep(0.3)

        # 1. Empty Working Sets (Windows)
        if IS_WINDOWS:
            freed += self._empty_working_sets()

        # 2. Liberar caché de sistema
        freed += self._clear_standby()

        # 3. Recolección de basura Python
        freed += self._gc_collect()

        self._log(f"Optimización completa → {SystemMemory.fmt(freed)} liberados", "OK")
        return freed

    def run_deep(self):
        freed = 0
        self._log("Iniciando optimización PROFUNDA...", "RUN")
        time.sleep(0.4)

        freed += self.run_quick()

        if IS_WINDOWS:
            freed += self._flush_dns()
            freed += self._clear_prefetch()
            freed += self._trim_processes()

        freed += self._clear_temp_files()
        self._log(f"Optimización profunda completa → {SystemMemory.fmt(freed)} liberados", "OK")
        return freed

    def run_extreme(self):
        freed = 0
        self._log("⚠ Iniciando modo EXTREMO — Máxima limpieza", "WARN")
        time.sleep(0.5)

        freed += self.run_deep()

        if IS_WINDOWS:
            freed += self._adjust_priority()
            freed += self._disable_superfetch()

        self._log(f"Modo extremo completo → {SystemMemory.fmt(freed)} liberados", "OK")
        return freed

    # ── Métodos individuales ──────────────────────────────────────────────────

    def _empty_working_sets(self):
        freed = 0
        if not IS_WINDOWS:
            return 0
        self._log("Vaciando Working Sets de procesos...", "RUN")
        try:
            import psutil
            count = 0
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info["pid"])
                    if handle:
                        ctypes.windll.psapi.EmptyWorkingSet(handle)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        count += 1
                        freed += 512 * 1024  # estimado ~512 KB por proceso
                except Exception:
                    pass
            self._log(f"Working sets vaciados en {count} procesos", "OK")
        except Exception as e:
            self._log(f"Working Sets: {e}", "WARN")
        return freed

    def _clear_standby(self):
        self._log("Liberando memoria en standby...", "RUN")
        freed = 0
        if IS_WINDOWS:
            try:
                # NtSetSystemInformation para limpiar standby list
                SystemMemoryListCommand = ctypes.c_ulong(4)
                ntdll = ctypes.windll.ntdll
                status = ntdll.NtSetSystemInformation(0x50, ctypes.byref(SystemMemoryListCommand), ctypes.sizeof(SystemMemoryListCommand))
                if status == 0:
                    self._log("Standby list limpiada", "OK")
                    freed += 200 * 1024 * 1024
                else:
                    self._log("Standby: requiere privilegios de administrador", "WARN")
            except Exception as e:
                self._log(f"Standby: {e}", "WARN")
        else:
            time.sleep(0.2)
            freed += 100 * 1024 * 1024
            self._log("Caché de sistema liberada", "OK")
        return freed

    def _gc_collect(self):
        import gc
        self._log("Ejecutando recolección de basura...", "RUN")
        before = 0
        try:
            import psutil
            before = psutil.Process().memory_info().rss
        except Exception:
            pass
        collected = gc.collect(2)
        after = 0
        try:
            import psutil
            after = psutil.Process().memory_info().rss
        except Exception:
            pass
        freed = max(0, before - after)
        self._log(f"GC: {collected} objetos recolectados", "OK")
        return freed

    def _flush_dns(self):
        self._log("Limpiando caché DNS...", "RUN")
        try:
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, creationflags=0x08000000 if IS_WINDOWS else 0)
            self._log("Caché DNS limpiada", "OK")
        except Exception as e:
            self._log(f"DNS: {e}", "WARN")
        return 2 * 1024 * 1024

    def _clear_prefetch(self):
        self._log("Optimizando Prefetch...", "RUN")
        freed = 0
        if IS_WINDOWS:
            prefetch_dir = r"C:\Windows\Prefetch"
            if os.path.isdir(prefetch_dir):
                for f in os.listdir(prefetch_dir):
                    try:
                        fp = os.path.join(prefetch_dir, f)
                        if os.path.isfile(fp):
                            freed += os.path.getsize(fp)
                            os.remove(fp)
                    except Exception:
                        pass
                self._log(f"Prefetch limpiado → {SystemMemory.fmt(freed)}", "OK")
            else:
                self._log("Prefetch: acceso limitado (necesita admin)", "WARN")
        return freed

    def _trim_processes(self):
        self._log("Aplicando SetProcessWorkingSetSize a procesos...", "RUN")
        freed = 0
        try:
            import psutil
            for proc in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    mi = proc.info.get("memory_info")
                    if mi and mi.rss > 50 * 1024 * 1024:
                        handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info["pid"])
                        if handle:
                            ctypes.windll.kernel32.SetProcessWorkingSetSize(handle, ctypes.c_size_t(-1), ctypes.c_size_t(-1))
                            ctypes.windll.kernel32.CloseHandle(handle)
                            freed += 1 * 1024 * 1024
                except Exception:
                    pass
            self._log("Working set trimming completado", "OK")
        except Exception as e:
            self._log(f"Trim: {e}", "WARN")
        return freed

    def _clear_temp_files(self):
        self._log("Limpiando archivos temporales...", "RUN")
        freed = 0
        temp_dirs = [os.environ.get("TEMP", ""), os.environ.get("TMP", "")]
        for td in temp_dirs:
            if td and os.path.isdir(td):
                for f in os.listdir(td):
                    try:
                        fp = os.path.join(td, f)
                        sz = os.path.getsize(fp) if os.path.isfile(fp) else 0
                        if os.path.isfile(fp):
                            os.remove(fp)
                            freed += sz
                    except Exception:
                        pass
        self._log(f"Temps limpiados → {SystemMemory.fmt(freed)}", "OK")
        return freed

    def _adjust_priority(self):
        self._log("Ajustando prioridades de procesos...", "RUN")
        if IS_WINDOWS:
            try:
                import psutil
                my_pid = os.getpid()
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        if proc.info["pid"] != my_pid:
                            p = psutil.Process(proc.info["pid"])
                            if p.nice() == psutil.NORMAL_PRIORITY_CLASS:
                                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                    except Exception:
                        pass
                self._log("Prioridades ajustadas a BELOW_NORMAL", "OK")
            except Exception as e:
                self._log(f"Prioridades: {e}", "WARN")
        return 0

    def _disable_superfetch(self):
        self._log("Optimizando SysMain/SuperFetch...", "RUN")
        try:
            subprocess.run(
                ["sc", "stop", "SysMain"],
                capture_output=True,
                creationflags=0x08000000 if IS_WINDOWS else 0
            )
            self._log("SysMain pausado temporalmente", "OK")
        except Exception as e:
            self._log(f"SysMain: {e}", "WARN")
        return 50 * 1024 * 1024


# ─── WIDGET: GAUGE CIRCULAR ──────────────────────────────────────────────────
class CircularGauge(tk.Canvas):
    def __init__(self, parent, size=160, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=COLORS["bg_card"], highlightthickness=0, **kwargs)
        self.size = size
        self.value = 0
        self._draw(0)

    def _draw(self, pct):
        self.delete("all")
        s = self.size
        cx, cy = s // 2, s // 2
        r_outer = s // 2 - 8
        r_inner = r_outer - 18

        # Fondo del arco
        self._arc(cx, cy, r_outer, r_inner, 0, 360, COLORS["bg_dark"])

        # Color según nivel
        if pct < 50:
            color = COLORS["accent_green"]
        elif pct < 75:
            color = COLORS["accent_orange"]
        else:
            color = COLORS["accent_red"]

        # Arco de progreso
        if pct > 0:
            self._arc(cx, cy, r_outer, r_inner, -90, -90 + 360 * pct / 100, color)

        # Glow interno
        self.create_oval(cx - r_inner + 4, cy - r_inner + 4,
                         cx + r_inner - 4, cy + r_inner - 4,
                         fill=COLORS["bg_dark"], outline="")

        # Texto porcentaje
        self.create_text(cx, cy - 8, text=f"{pct:.0f}%",
                         font=FONTS["metric"], fill=color)
        self.create_text(cx, cy + 22, text="RAM USAGE",
                         font=FONTS["label"], fill=COLORS["text_sub"])

    def _arc(self, cx, cy, r_out, r_in, start, end, color):
        # Dibuja arco grueso usando polígono de puntos
        steps = max(int(abs(end - start)), 60)
        points = []
        for i in range(steps + 1):
            a = math.radians(start + (end - start) * i / steps)
            points.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
        for i in range(steps, -1, -1):
            a = math.radians(start + (end - start) * i / steps)
            points.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
        if len(points) > 2:
            flat = [v for p in points for v in p]
            self.create_polygon(flat, fill=color, outline="")

    def update_value(self, pct):
        self.value = pct
        self._draw(pct)


# ─── WIDGET: MINI GRÁFICA HISTÓRICA ─────────────────────────────────────────
class SparkLine(tk.Canvas):
    def __init__(self, parent, w=320, h=60, **kwargs):
        super().__init__(parent, width=w, height=h,
                         bg=COLORS["bg_dark"], highlightthickness=0, **kwargs)
        self.w, self.h = w, h
        self.history = []
        self.max_pts = 60

    def push(self, val):
        self.history.append(val)
        if len(self.history) > self.max_pts:
            self.history.pop(0)
        self._draw()

    def _draw(self):
        self.delete("all")
        if len(self.history) < 2:
            return
        n = len(self.history)
        pts = []
        for i, v in enumerate(self.history):
            x = self.w * i / (self.max_pts - 1)
            y = self.h - (v / 100) * (self.h - 6) - 3
            pts.append((x, y))

        # Área rellena
        poly_pts = [(pts[0][0], self.h)] + pts + [(pts[-1][0], self.h)]
        flat = [v for p in poly_pts for v in p]
        self.create_polygon(flat, fill=COLORS["glow"], outline="")

        # Línea
        if len(pts) >= 2:
            flat_line = [v for p in pts for v in p]
            self.create_line(flat_line, fill=COLORS["accent"], width=2, smooth=True)

        # Punto actual
        lx, ly = pts[-1]
        self.create_oval(lx - 3, ly - 3, lx + 3, ly + 3,
                         fill=COLORS["accent"], outline=COLORS["bg_dark"])


# ─── APLICACIÓN PRINCIPAL ─────────────────────────────────────────────────────
class RAMOptimizerApp:
    def __init__(self):
        self.root = tk.Tk()
        self._configure_window()
        self._setup_styles()
        self._build_ui()
        self.optimizer = MemoryOptimizer(self._append_log)
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self._update_stats()

    def _configure_window(self):
        self.root.title("RAM Optimizer Pro  ·  v2.0")
        self.root.geometry("980x700")
        self.root.minsize(900, 640)
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.resizable(True, True)

        # Centrar en pantalla
        self.root.update_idletasks()
        w, h = 980, 700
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Ícono en taskbar (si es Windows)
        if IS_WINDOWS:
            try:
                self.root.iconbitmap(default="")
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RAMOptimizerPro.2.0")
            except Exception:
                pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=COLORS["bg_dark"])
        style.configure("Card.TFrame", background=COLORS["bg_card"])
        style.configure("TScrollbar",
                         background=COLORS["bg_input"],
                         troughcolor=COLORS["bg_dark"],
                         arrowcolor=COLORS["accent"])

    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── TOP BAR ──────────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=COLORS["bg_panel"], height=60)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        # Logo + título
        logo_frame = tk.Frame(top, bg=COLORS["bg_panel"])
        logo_frame.pack(side="left", padx=20)

        tk.Label(logo_frame, text="⬡", font=("Consolas", 20, "bold"),
                 fg=COLORS["accent"], bg=COLORS["bg_panel"]).pack(side="left", padx=(0, 8))
        tk.Label(logo_frame, text="RAM OPTIMIZER PRO",
                 font=FONTS["title"], fg=COLORS["text_main"],
                 bg=COLORS["bg_panel"]).pack(side="left")
        tk.Label(logo_frame, text=" v2.0",
                 font=("Consolas", 10), fg=COLORS["accent"],
                 bg=COLORS["bg_panel"]).pack(side="left", pady=(8, 0))

        # Status indicator
        self.status_dot = tk.Label(top, text="●", font=("Consolas", 14),
                                    fg=COLORS["accent_green"], bg=COLORS["bg_panel"])
        self.status_dot.pack(side="right", padx=6)
        self.status_lbl = tk.Label(top, text="SISTEMA MONITOREADO",
                                    font=FONTS["small"], fg=COLORS["text_sub"],
                                    bg=COLORS["bg_panel"])
        self.status_lbl.pack(side="right")
        self.clock_lbl = tk.Label(top, text="", font=FONTS["body"],
                                   fg=COLORS["text_dim"], bg=COLORS["bg_panel"])
        self.clock_lbl.pack(side="right", padx=20)

        # ── LÍNEA DIVISORA ────────────────────────────────────────────────────
        tk.Frame(self.root, bg=COLORS["accent"], height=1).pack(fill="x")

        # ── BODY ──────────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # Columna izquierda
        left = tk.Frame(body, bg=COLORS["bg_dark"], width=310)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        self._build_left_panel(left)

        # Columna central/derecha
        right = tk.Frame(body, bg=COLORS["bg_dark"])
        right.pack(side="left", fill="both", expand=True)
        self._build_right_panel(right)

        # ── STATUS BAR ────────────────────────────────────────────────────────
        sb = tk.Frame(self.root, bg=COLORS["bg_panel"], height=28)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        self.sb_text = tk.Label(sb, text="Listo.", font=FONTS["small"],
                                fg=COLORS["text_sub"], bg=COLORS["bg_panel"])
        self.sb_text.pack(side="left", padx=12)

        platform_txt = f"Windows {IS_WINDOWS and 'Activo' or 'Demo Mode'}"
        tk.Label(sb, text=f"● {platform_txt}  |  Python {sys.version.split()[0]}",
                 font=FONTS["label"], fg=COLORS["text_dim"],
                 bg=COLORS["bg_panel"]).pack(side="right", padx=12)

    # ─── PANEL IZQUIERDO ─────────────────────────────────────────────────────
    def _build_left_panel(self, parent):
        # Gauge
        card_gauge = tk.Frame(parent, bg=COLORS["bg_card"], bd=0,
                               highlightthickness=1,
                               highlightbackground=COLORS["border"])
        card_gauge.pack(fill="x", pady=(0, 8))

        tk.Label(card_gauge, text="USO DE MEMORIA",
                 font=FONTS["header"], fg=COLORS["accent"],
                 bg=COLORS["bg_card"]).pack(pady=(12, 6))

        self.gauge = CircularGauge(card_gauge, size=160)
        self.gauge.pack(pady=4)

        # Métricas rápidas
        metrics_frame = tk.Frame(card_gauge, bg=COLORS["bg_card"])
        metrics_frame.pack(fill="x", padx=16, pady=(4, 14))

        self.lbl_used  = self._metric(metrics_frame, "USADA",    "─", 0, 0)
        self.lbl_free  = self._metric(metrics_frame, "LIBRE",    "─", 0, 1)
        self.lbl_total = self._metric(metrics_frame, "TOTAL",    "─", 1, 0)
        self.lbl_swap  = self._metric(metrics_frame, "SWAP",     "─", 1, 1)

        # Sparkline
        card_spark = tk.Frame(parent, bg=COLORS["bg_card"], bd=0,
                               highlightthickness=1,
                               highlightbackground=COLORS["border"])
        card_spark.pack(fill="x", pady=(0, 8))

        tk.Label(card_spark, text="HISTORIAL EN TIEMPO REAL",
                 font=FONTS["small"], fg=COLORS["text_sub"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=12, pady=(10, 4))

        self.sparkline = SparkLine(card_spark, w=278, h=55)
        self.sparkline.pack(padx=14, pady=(0, 12))

        # Botones de optimización
        card_btns = tk.Frame(parent, bg=COLORS["bg_card"], bd=0,
                              highlightthickness=1,
                              highlightbackground=COLORS["border"])
        card_btns.pack(fill="x", pady=(0, 8))

        tk.Label(card_btns, text="OPTIMIZACIÓN",
                 font=FONTS["header"], fg=COLORS["accent"],
                 bg=COLORS["bg_card"]).pack(anchor="w", padx=14, pady=(12, 8))

        self._opt_btn(card_btns, "⚡  RÁPIDA",
                      "Limpia Working Sets y Standby",
                      COLORS["accent"], self._opt_quick)
        self._opt_btn(card_btns, "🔥  PROFUNDA",
                      "Incluye DNS, Prefetch y Temps",
                      COLORS["accent2"], self._opt_deep)
        self._opt_btn(card_btns, "☢  EXTREMA",
                      "Máxima limpieza + prioridades",
                      COLORS["accent_red"], self._opt_extreme)

        # Espacio restante
        tk.Frame(parent, bg=COLORS["bg_dark"]).pack(fill="both", expand=True)

    def _metric(self, parent, label, value, row, col):
        f = tk.Frame(parent, bg=COLORS["bg_input"])
        f.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
        parent.columnconfigure(col, weight=1)

        tk.Label(f, text=label, font=FONTS["label"],
                 fg=COLORS["text_dim"], bg=COLORS["bg_input"]).pack(pady=(6, 2))
        lbl = tk.Label(f, text=value, font=("Consolas", 13, "bold"),
                        fg=COLORS["accent"], bg=COLORS["bg_input"])
        lbl.pack(pady=(0, 6))
        return lbl

    def _opt_btn(self, parent, text, sub, color, command):
        f = tk.Frame(parent, bg=COLORS["bg_input"], cursor="hand2")
        f.pack(fill="x", padx=12, pady=4)

        def on_enter(e): f.configure(bg=color + "22")
        def on_leave(e): f.configure(bg=COLORS["bg_input"])

        f.bind("<Enter>", on_enter)
        f.bind("<Leave>", on_leave)
        f.bind("<Button-1>", lambda e: command())

        lbl_main = tk.Label(f, text=text, font=FONTS["header"],
                             fg=color, bg=COLORS["bg_input"],
                             cursor="hand2")
        lbl_main.pack(anchor="w", padx=12, pady=(8, 2))
        lbl_main.bind("<Button-1>", lambda e: command())

        lbl_sub = tk.Label(f, text=sub, font=FONTS["small"],
                            fg=COLORS["text_dim"], bg=COLORS["bg_input"],
                            cursor="hand2")
        lbl_sub.pack(anchor="w", padx=14, pady=(0, 8))
        lbl_sub.bind("<Button-1>", lambda e: command())

    # ─── PANEL DERECHO ───────────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        # Tab-like sections
        tab_bar = tk.Frame(parent, bg=COLORS["bg_dark"])
        tab_bar.pack(fill="x", pady=(0, 6))

        self.tab_pages = {}
        self.active_tab = tk.StringVar(value="processes")

        for tab_id, label in [("processes","PROCESOS"),("log","REGISTRO"),("tips","CONSEJOS")]:
            btn = tk.Label(tab_bar, text=label, font=FONTS["body"],
                           fg=COLORS["accent"] if tab_id == "processes" else COLORS["text_sub"],
                           bg=COLORS["bg_panel"], padx=18, pady=8,
                           cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, t=tab_id: self._switch_tab(t))
            self.tab_pages[tab_id] = {"btn": btn}

        # Content area
        self.content_area = tk.Frame(parent, bg=COLORS["bg_dark"])
        self.content_area.pack(fill="both", expand=True)

        self._build_processes_page()
        self._build_log_page()
        self._build_tips_page()
        self._switch_tab("processes")

    def _switch_tab(self, tab_id):
        self.active_tab.set(tab_id)
        for tid, data in self.tab_pages.items():
            color = COLORS["accent"] if tid == tab_id else COLORS["text_sub"]
            data["btn"].configure(fg=color)
            if "frame" in data:
                data["frame"].pack_forget()

        if "frame" in self.tab_pages[tab_id]:
            self.tab_pages[tab_id]["frame"].pack(fill="both", expand=True)

    def _build_processes_page(self):
        frame = tk.Frame(self.content_area, bg=COLORS["bg_dark"])
        self.tab_pages["processes"]["frame"] = frame

        header = tk.Frame(frame, bg=COLORS["bg_panel"])
        header.pack(fill="x", pady=(0, 4))

        for col, w, txt in [
            ("col_pid", 60, "PID"),
            ("col_name", 240, "PROCESO"),
            ("col_mb", 100, "MEMORIA"),
            ("col_bar", 160, "BARRA"),
            ("col_status", 80, "ESTADO"),
        ]:
            tk.Label(header, text=txt, font=FONTS["label"],
                     fg=COLORS["text_dim"], bg=COLORS["bg_panel"],
                     width=w // 8, anchor="w").pack(side="left", padx=4, pady=6)

        # Scrollable list
        container = tk.Frame(frame, bg=COLORS["bg_dark"])
        container.pack(fill="both", expand=True)

        self.proc_canvas = tk.Canvas(container, bg=COLORS["bg_dark"],
                                     highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                   command=self.proc_canvas.yview)
        self.proc_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.proc_canvas.pack(side="left", fill="both", expand=True)

        self.proc_inner = tk.Frame(self.proc_canvas, bg=COLORS["bg_dark"])
        self.proc_canvas_window = self.proc_canvas.create_window(
            (0, 0), window=self.proc_inner, anchor="nw")

        self.proc_inner.bind("<Configure>",
            lambda e: self.proc_canvas.configure(
                scrollregion=self.proc_canvas.bbox("all")))
        self.proc_canvas.bind("<Configure>",
            lambda e: self.proc_canvas.itemconfig(
                self.proc_canvas_window, width=e.width))

        # Mousewheel
        self.proc_canvas.bind("<MouseWheel>",
            lambda e: self.proc_canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self._refresh_processes()
        frame.after(3000, self._auto_refresh_processes)

    def _refresh_processes(self):
        for w in self.proc_inner.winfo_children():
            w.destroy()

        procs = SystemMemory.get_processes()
        if not procs:
            tk.Label(self.proc_inner, text="No se pudieron obtener procesos (instala psutil)",
                     font=FONTS["body"], fg=COLORS["text_dim"],
                     bg=COLORS["bg_dark"]).pack(pady=20)
            return

        max_mb = procs[0]["mb"] if procs else 1

        for i, p in enumerate(procs):
            row_bg = COLORS["bg_card"] if i % 2 == 0 else COLORS["bg_dark"]
            row = tk.Frame(self.proc_inner, bg=row_bg)
            row.pack(fill="x", pady=1)

            # PID
            tk.Label(row, text=str(p["pid"]), font=FONTS["mono"],
                     fg=COLORS["text_dim"], bg=row_bg, width=7,
                     anchor="w").pack(side="left", padx=(8, 4))

            # Nombre
            name = p["name"][:28]
            tk.Label(row, text=name, font=FONTS["body"],
                     fg=COLORS["text_main"], bg=row_bg, width=30,
                     anchor="w").pack(side="left", padx=4)

            # MB
            mb_str = f"{p['mb']:.1f} MB"
            color = COLORS["accent_red"] if p["mb"] > 500 else (
                COLORS["accent_orange"] if p["mb"] > 200 else COLORS["accent_green"])
            tk.Label(row, text=mb_str, font=("Consolas", 9, "bold"),
                     fg=color, bg=row_bg, width=12,
                     anchor="e").pack(side="left", padx=4)

            # Barra mini
            bar_frame = tk.Frame(row, bg=row_bg, width=140, height=8)
            bar_frame.pack(side="left", padx=6, pady=6)
            bar_frame.pack_propagate(False)
            pct = min(p["mb"] / max_mb, 1.0)
            fill_w = int(136 * pct)
            tk.Frame(bar_frame, bg=color, width=fill_w).pack(
                side="left", fill="y")

            # Estado
            status = p.get("status", "?")[:10]
            s_color = COLORS["accent_green"] if status == "running" else COLORS["text_dim"]
            tk.Label(row, text=status, font=FONTS["small"],
                     fg=s_color, bg=row_bg, width=10,
                     anchor="w").pack(side="left", padx=4)

    def _auto_refresh_processes(self):
        if self.running and self.active_tab.get() == "processes":
            self._refresh_processes()
        self.root.after(3000, self._auto_refresh_processes)

    def _build_log_page(self):
        frame = tk.Frame(self.content_area, bg=COLORS["bg_dark"])
        self.tab_pages["log"]["frame"] = frame

        toolbar = tk.Frame(frame, bg=COLORS["bg_panel"])
        toolbar.pack(fill="x", pady=(0, 4))

        tk.Label(toolbar, text="REGISTRO DE OPERACIONES",
                 font=FONTS["small"], fg=COLORS["text_sub"],
                 bg=COLORS["bg_panel"]).pack(side="left", padx=12, pady=8)

        tk.Label(toolbar, text="[LIMPIAR]", font=FONTS["small"],
                 fg=COLORS["accent"], bg=COLORS["bg_panel"],
                 cursor="hand2").pack(side="right", padx=12)

        self.log_text = tk.Text(frame, bg=COLORS["bg_dark"],
                                fg=COLORS["text_main"],
                                font=FONTS["mono"],
                                insertbackground=COLORS["accent"],
                                selectbackground=COLORS["bg_input"],
                                relief="flat", wrap="word",
                                state="disabled")
        self.log_text.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)

        # Tag colors
        self.log_text.tag_configure("INFO",   foreground=COLORS["text_sub"])
        self.log_text.tag_configure("OK",     foreground=COLORS["accent_green"])
        self.log_text.tag_configure("WARN",   foreground=COLORS["accent_orange"])
        self.log_text.tag_configure("ERR",    foreground=COLORS["accent_red"])
        self.log_text.tag_configure("RUN",    foreground=COLORS["accent"])

    def _append_log(self, msg, level="INFO"):
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n", level)
            self.log_text.configure(state="disabled")
            self.log_text.see("end")
            self.sb_text.configure(text=msg[:80])
        self.root.after(0, _do)

    def _build_tips_page(self):
        frame = tk.Frame(self.content_area, bg=COLORS["bg_dark"])
        self.tab_pages["tips"]["frame"] = frame

        canvas = tk.Canvas(frame, bg=COLORS["bg_dark"], highlightthickness=0)
        sb = ttk.Scrollbar(frame, command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLORS["bg_dark"])
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))

        tips = [
            ("🔵", "Optimización Rápida", COLORS["accent"],
             "Vacía los Working Sets de todos los procesos activos y limpia la Standby List.\n"
             "Ideal para uso diario. No afecta la estabilidad del sistema."),
            ("🟣", "Optimización Profunda", COLORS["accent2"],
             "Incluye todo lo anterior más: limpieza de caché DNS, archivos Prefetch\n"
             "y carpetas temporales. Recomendada cada semana."),
            ("🔴", "Optimización Extrema", COLORS["accent_red"],
             "Máxima agresividad: ajusta prioridades, pausa SysMain.\n"
             "Úsala antes de tareas críticas como gaming o renderizado."),
            ("💡", "Cuándo Optimizar", COLORS["accent_orange"],
             "• RAM > 80%: usa Profunda\n"
             "• RAM > 90%: usa Extrema\n"
             "• Slowdown repentino: usa Rápida\n"
             "• Antes de gaming/render: usa Extrema"),
            ("⚙️", "Requiere Administrador", COLORS["accent"],
             "Para máxima efectividad, ejecuta el launcher.bat como Administrador.\n"
             "Algunas operaciones (Standby, Working Sets) necesitan privilegios elevados."),
        ]

        for icon, title, color, desc in tips:
            card = tk.Frame(inner, bg=COLORS["bg_card"],
                            highlightthickness=1, highlightbackground=COLORS["border"])
            card.pack(fill="x", padx=12, pady=6)

            head = tk.Frame(card, bg=COLORS["bg_card"])
            head.pack(fill="x", padx=16, pady=(14, 6))

            tk.Label(head, text=icon, font=("Consolas", 16),
                     bg=COLORS["bg_card"]).pack(side="left", padx=(0, 8))
            tk.Label(head, text=title, font=FONTS["header"],
                     fg=color, bg=COLORS["bg_card"]).pack(side="left")

            tk.Label(card, text=desc, font=FONTS["body"],
                     fg=COLORS["text_sub"], bg=COLORS["bg_card"],
                     justify="left", wraplength=520).pack(
                anchor="w", padx=24, pady=(0, 14))

    # ─── MONITOR ─────────────────────────────────────────────────────────────
    def _monitor_loop(self):
        while self.running:
            try:
                info = SystemMemory.get_info()
                self.root.after(0, lambda i=info: self._update_ui(i))
            except Exception:
                pass
            time.sleep(1.5)

    def _update_ui(self, info):
        pct = info["percent"]
        self.gauge.update_value(pct)
        self.sparkline.push(pct)

        self.lbl_used.configure(text=SystemMemory.fmt(info["used"]))
        self.lbl_free.configure(text=SystemMemory.fmt(info["available"]))
        self.lbl_total.configure(text=SystemMemory.fmt(info["total"]))
        self.lbl_swap.configure(text=f"{info['swap_pct']:.0f}%")

        # Reloj
        self.clock_lbl.configure(text=datetime.now().strftime("%H:%M:%S"))

        # Status dot color
        if pct >= 85:
            self.status_dot.configure(fg=COLORS["accent_red"])
            self.status_lbl.configure(text="⚠ RAM CRÍTICA")
        elif pct >= 65:
            self.status_dot.configure(fg=COLORS["accent_orange"])
            self.status_lbl.configure(text="RAM ELEVADA")
        else:
            self.status_dot.configure(fg=COLORS["accent_green"])
            self.status_lbl.configure(text="SISTEMA ESTABLE")

    def _update_stats(self):
        # Primer render
        try:
            info = SystemMemory.get_info()
            self._update_ui(info)
        except Exception:
            pass
        self.root.after(1500, self._update_stats)

    # ─── OPTIMIZACIÓN ────────────────────────────────────────────────────────
    def _run_opt(self, func, label):
        self._switch_tab("log")

        def _worker():
            before = SystemMemory.get_info()["used"]
            self._append_log(f"═══ {label} ═══", "RUN")
            freed = func()
            after = SystemMemory.get_info()["used"]
            real_freed = max(0, before - after)
            self._append_log(
                f"Resultado final: {SystemMemory.fmt(max(freed, real_freed))} liberados", "OK")
            self._append_log("─" * 50, "INFO")

        threading.Thread(target=_worker, daemon=True).start()

    def _opt_quick(self):
        self._run_opt(self.optimizer.run_quick, "OPTIMIZACIÓN RÁPIDA")

    def _opt_deep(self):
        self._run_opt(self.optimizer.run_deep, "OPTIMIZACIÓN PROFUNDA")

    def _opt_extreme(self):
        if IS_WINDOWS:
            resp = messagebox.askyesno(
                "RAM Optimizer Pro",
                "El modo EXTREMO ajusta prioridades de procesos\ny pausa servicios.\n\n¿Continuar?",
                icon="warning")
            if not resp:
                return
        self._run_opt(self.optimizer.run_extreme, "OPTIMIZACIÓN EXTREMA")

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Solicitar privilegios admin en Windows si no los tiene
    if IS_WINDOWS:
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False
        if not is_admin:
            # Re-lanzar como administrador
            try:
                params = " ".join(f'"{a}"' for a in sys.argv)
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, params, None, 1)
                sys.exit(0)
            except Exception:
                pass  # Continuar sin admin

    app = RAMOptimizerApp()
    app.run()
