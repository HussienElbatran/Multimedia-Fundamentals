import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
import sys
import threading

# optional heavy imports (install with pip) 
try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import cv2
    import numpy as np
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    from pydub import AudioSegment
    from pydub.playback import play
    AUDIO_OK = True
except ImportError:
    AUDIO_OK = False

# ------------------------------------------------------------------------------
COLORS = {
    "bg": "#1a1a2e",
    "panel": "#16213e",
    "accent": "#0f3460",
    "highlight": "#e94560",
    "text": "#eaeaea",
    "subtext": "#a0a0b0",
    "btn": "#e94560",
    "btn_hover": "#c73652",
    "success": "#4caf50",
    "warning": "#ff9800",
}

IMAGE_EXT  = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp", ".ico"}
AUDIO_EXT  = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}
VIDEO_EXT  = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
TEXT_EXT   = {".txt", ".csv", ".log", ".json", ".xml", ".html", ".md", ".py",
              ".js", ".css", ".java", ".c", ".cpp", ".h"}


def file_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:  return "image"
    if ext in AUDIO_EXT:  return "audio"
    if ext in VIDEO_EXT:  return "video"
    if ext in TEXT_EXT:   return "text"
    return "unknown"

#-------------------------------------------------------------------------------

#  MAIN APPLICATION

class MultimediaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎬 Multimedia File Manipulator")
        self.geometry("1000x700")
        self.minsize(900, 620)
        self.configure(bg=COLORS["bg"])
        self._current_path = tk.StringVar()
        self._status      = tk.StringVar(value="Browse a file to get started …")
        self._build_ui()

    #  UI scaffolding 
    def _build_ui(self):
        #  header
        hdr = tk.Frame(self, bg=COLORS["accent"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎬 Multimedia File Manipulator",
                 font=("Segoe UI", 20, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text"]).pack()
        tk.Label(hdr, text="Load any file — manipulate it instantly",
                 font=("Segoe UI", 10), bg=COLORS["accent"],
                 fg=COLORS["subtext"]).pack()

        # file picker row
        picker = tk.Frame(self, bg=COLORS["bg"], pady=10, padx=20)
        picker.pack(fill="x")
        tk.Label(picker, text="File:", bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Segoe UI", 11)).pack(side="left")
        entry = tk.Entry(picker, textvariable=self._current_path,
                         font=("Segoe UI", 11), bg=COLORS["panel"],
                         fg=COLORS["text"], insertbackground=COLORS["text"],
                         relief="flat", bd=6)
        entry.pack(side="left", fill="x", expand=True, padx=8)
        self._styled_btn(picker, "Browse", self._browse).pack(side="left", padx=4)
        self._styled_btn(picker, "Load ▶", self._load_file,
                         color=COLORS["success"]).pack(side="left", padx=4)

        # main body (left panel + right canvas)
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=6)

        # left: tool panel
        self._tool_frame = tk.Frame(body, bg=COLORS["panel"], width=260,
                                    relief="flat", bd=0)
        self._tool_frame.pack(side="left", fill="y", padx=(0, 8))
        self._tool_frame.pack_propagate(False)

        # right: output / preview
        right = tk.Frame(body, bg=COLORS["panel"], relief="flat")
        right.pack(side="left", fill="both", expand=True)

        self._preview_label = tk.Label(right, bg=COLORS["panel"],
                                       fg=COLORS["subtext"],
                                       font=("Segoe UI", 12),
                                       text="Preview / Output will appear here",
                                       wraplength=600, justify="left",
                                       anchor="nw")
        self._preview_label.pack(fill="both", expand=True, padx=10, pady=10)

        self._text_output = tk.Text(right, bg=COLORS["panel"], fg=COLORS["text"],
                                    font=("Consolas", 10), relief="flat",
                                    state="disabled", wrap="word")

        # status bar
        tk.Label(self, textvariable=self._status, bg=COLORS["accent"],
                 fg=COLORS["subtext"], font=("Segoe UI", 9), anchor="w",
                 padx=12).pack(fill="x", side="bottom")

    def _styled_btn(self, parent, text, cmd, color=None):
        c = color or COLORS["btn"]
        b = tk.Button(parent, text=text, command=cmd, bg=c, fg="white",
                      font=("Segoe UI", 10, "bold"), relief="flat",
                      padx=14, pady=6, cursor="hand2",
                      activebackground=COLORS["btn_hover"],
                      activeforeground="white", bd=0)
        b.bind("<Enter>", lambda e: b.config(bg=COLORS["btn_hover"]))
        b.bind("<Leave>", lambda e: b.config(bg=c))
        return b

    def _section(self, title):
        tk.Label(self._tool_frame, text=title, bg=COLORS["panel"],
                 fg=COLORS["highlight"], font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill="x", padx=10, pady=(12, 2))
        tk.Frame(self._tool_frame, bg=COLORS["highlight"], height=1
                 ).pack(fill="x", padx=10)

    def _tool_btn(self, text, cmd):
        b = tk.Button(self._tool_frame, text=text, command=cmd,
                      bg=COLORS["accent"], fg=COLORS["text"],
                      font=("Segoe UI", 9), relief="flat",
                      padx=8, pady=5, anchor="w", cursor="hand2",
                      activebackground=COLORS["highlight"],
                      activeforeground="white", bd=0)
        b.pack(fill="x", padx=10, pady=2)
        b.bind("<Enter>", lambda e: b.config(bg=COLORS["highlight"]))
        b.bind("<Leave>", lambda e: b.config(bg=COLORS["accent"]))
        return b

    # clear helpers 
    def _clear_tools(self):
        for w in self._tool_frame.winfo_children():
            w.destroy()

    def _clear_preview(self):
        self._preview_label.config(image="", text="")
        self._preview_label._img = None
        self._text_output.pack_forget()
        self._preview_label.pack(fill="both", expand=True, padx=10, pady=10)

    # file loading 
    def _browse(self):
        p = filedialog.askopenfilename(title="Select a file")
        if p:
            self._current_path.set(p)
            self._load_file()

    def _load_file(self):
        path = self._current_path.get().strip()
        if not os.path.isfile(path):
            messagebox.showerror("Error", "File not found.")
            return
        self._path = path
        self._ftype = file_type(path)
        self._clear_tools()
        self._clear_preview()
        self._status.set(f"Loaded: {os.path.basename(path)}  [{self._ftype.upper()}]")

        handlers = {
            "image":   self._setup_image,
            "audio":   self._setup_audio,
            "video":   self._setup_video,
            "text":    self._setup_text,
            "unknown": self._setup_unknown,
        }
        handlers[self._ftype]()

    
    #  IMAGE TOOLS
    
    def _setup_image(self):
        if not PIL_OK:
            self._show_text("Pillow not installed.\nRun: pip install pillow")
            return
        self._img_original = Image.open(self._path)
        self._img_current  = self._img_original.copy()
        self._show_image(self._img_current)

        self._section("📐 Transform")
        self._tool_btn("Rotate 90°",      lambda: self._img_op("rotate90"))
        self._tool_btn("Rotate 180°",     lambda: self._img_op("rotate180"))
        self._tool_btn("Flip Horizontal", lambda: self._img_op("flip_h"))
        self._tool_btn("Flip Vertical",   lambda: self._img_op("flip_v"))

        self._section("🎨 Color")
        self._tool_btn("Grayscale",   lambda: self._img_op("gray"))
        self._tool_btn("Invert",      lambda: self._img_op("invert"))
        self._tool_btn("Sepia",       lambda: self._img_op("sepia"))
        self._tool_btn("Enhance Brightness", self._img_brightness)
        self._tool_btn("Enhance Contrast",   self._img_contrast)

        self._section("🔎 Filters")
        self._tool_btn("Blur",        lambda: self._img_op("blur"))
        self._tool_btn("Sharpen",     lambda: self._img_op("sharpen"))
        self._tool_btn("Edge Detect", lambda: self._img_op("edges"))
        self._tool_btn("Emboss",      lambda: self._img_op("emboss"))

        self._section("💾 Export")
        self._tool_btn("Resize …",         self._img_resize_dialog)
        self._tool_btn("Save As …",        self._img_save)
        self._tool_btn("Reset to Original",lambda: self._img_op("reset"))
        self._tool_btn("File Info",        self._img_info)

    def _img_op(self, op):
        img = self._img_current
        orig = self._img_original
        ops = {
            "rotate90":  lambda: img.rotate(-90, expand=True),
            "rotate180": lambda: img.rotate(180),
            "flip_h":    lambda: ImageOps.mirror(img),
            "flip_v":    lambda: ImageOps.flip(img),
            "gray":      lambda: img.convert("L").convert("RGB"),
            "invert":    lambda: ImageOps.invert(img.convert("RGB")),
            "blur":      lambda: img.filter(ImageFilter.GaussianBlur(2)),
            "sharpen":   lambda: img.filter(ImageFilter.SHARPEN),
            "edges":     lambda: img.filter(ImageFilter.FIND_EDGES),
            "emboss":    lambda: img.filter(ImageFilter.EMBOSS),
            "reset":     lambda: orig.copy(),
        }
        if op == "sepia":
            gray = img.convert("L")
            sepia = Image.merge("RGB", [
                gray.point(lambda p: min(int(p * 1.08), 255)),
                gray.point(lambda p: min(int(p * 0.84), 255)),
                gray.point(lambda p: min(int(p * 0.66), 255)),
            ])
            self._img_current = sepia
        elif op in ops:
            self._img_current = ops[op]()
        self._show_image(self._img_current)

    def _img_brightness(self):
        self._enhance_dialog("Brightness", ImageEnhance.Brightness)

    def _img_contrast(self):
        self._enhance_dialog("Contrast", ImageEnhance.Contrast)

    def _enhance_dialog(self, name, Enhancer):
        d = tk.Toplevel(self); d.title(name); d.configure(bg=COLORS["bg"])
        d.resizable(False, False)
        tk.Label(d, text=f"Factor (0.1 – 3.0):", bg=COLORS["bg"],
                 fg=COLORS["text"], font=("Segoe UI", 10)).pack(padx=20, pady=(16,4))
        var = tk.DoubleVar(value=1.0)
        scale = ttk.Scale(d, from_=0.1, to=3.0, variable=var, orient="horizontal",
                          length=260)
        scale.pack(padx=20)
        lbl = tk.Label(d, textvariable=var, bg=COLORS["bg"], fg=COLORS["highlight"])
        lbl.pack()
        def apply():
            self._img_current = Enhancer(self._img_current).enhance(var.get())
            self._show_image(self._img_current); d.destroy()
        tk.Button(d, text="Apply", command=apply, bg=COLORS["btn"], fg="white",
                  relief="flat", padx=16, pady=6).pack(pady=12)

    def _img_resize_dialog(self):
        d = tk.Toplevel(self); d.title("Resize Image"); d.configure(bg=COLORS["bg"])
        d.resizable(False, False)
        w_var = tk.IntVar(value=self._img_current.width)
        h_var = tk.IntVar(value=self._img_current.height)
        for label, var in [("Width (px):", w_var), ("Height (px):", h_var)]:
            row = tk.Frame(d, bg=COLORS["bg"]); row.pack(padx=20, pady=4, fill="x")
            tk.Label(row, text=label, bg=COLORS["bg"], fg=COLORS["text"],
                     width=12, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg=COLORS["panel"], fg=COLORS["text"],
                     width=8, relief="flat").pack(side="left")
        def apply():
            self._img_current = self._img_current.resize(
                (w_var.get(), h_var.get()), Image.LANCZOS)
            self._show_image(self._img_current); d.destroy()
        tk.Button(d, text="Resize", command=apply, bg=COLORS["btn"], fg="white",
                  relief="flat", padx=16, pady=6).pack(pady=12)

    def _img_save(self):
        ext = os.path.splitext(self._path)[1]
        out = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[("JPEG","*.jpg"),("PNG","*.png"),("BMP","*.bmp"),
                       ("All","*.*")])
        if out:
            self._img_current.save(out)
            self._status.set(f"Saved → {out}")

    def _img_info(self):
        img = self._img_original
        info = (f"File:   {os.path.basename(self._path)}\n"
                f"Size:   {img.size[0]} × {img.size[1]} px\n"
                f"Mode:   {img.mode}\n"
                f"Format: {img.format}\n"
                f"Bytes:  {os.path.getsize(self._path):,}")
        messagebox.showinfo("Image Info", info)

    def _show_image(self, img):
        self._text_output.pack_forget()
        self._preview_label.pack(fill="both", expand=True, padx=10, pady=10)
        # fit to panel
        max_w, max_h = 680, 540
        ratio = min(max_w / img.width, max_h / img.height, 1)
        disp = img.resize((int(img.width * ratio), int(img.height * ratio)),
                           Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(disp)
        self._preview_label.config(image=tk_img, text="")
        self._preview_label._img = tk_img

    
    #  AUDIO TOOLS
    
    def _setup_audio(self):
        info = self._audio_info_str()
        self._show_text(info)

        self._section("🔊 Audio Info")
        self._tool_btn("Show Info",   self._show_audio_info)

        self._section("✂️  Edit")
        self._tool_btn("Trim (start/end)",  self._audio_trim)
        self._tool_btn("Change Volume",     self._audio_volume)
        self._tool_btn("Reverse Audio",     self._audio_reverse)

        self._section("💾 Export")
        self._tool_btn("Export as WAV",  lambda: self._audio_export("wav"))
        self._tool_btn("Export as MP3",  lambda: self._audio_export("mp3"))
        self._tool_btn("Export as OGG",  lambda: self._audio_export("ogg"))

    def _load_audio(self):
        if not AUDIO_OK:
            messagebox.showerror("Missing Library",
                "pydub not installed.\nRun: pip install pydub\n"
                "Also requires ffmpeg in PATH.")
            return None
        return AudioSegment.from_file(self._path)

    def _audio_info_str(self):
        size = os.path.getsize(self._path)
        lines = [f"File:       {os.path.basename(self._path)}",
                 f"Size:       {size:,} bytes ({size/1024/1024:.2f} MB)",
                 f"Extension:  {os.path.splitext(self._path)[1].upper()}"]
        if AUDIO_OK:
            try:
                seg = AudioSegment.from_file(self._path)
                dur = len(seg) / 1000
                lines += [f"Duration:   {dur:.2f} s  ({int(dur//60)}m {int(dur%60)}s)",
                          f"Channels:   {seg.channels}",
                          f"Frame Rate: {seg.frame_rate} Hz",
                          f"Sample Wid: {seg.sample_width * 8} bit"]
            except Exception as e:
                lines.append(f"(Could not read audio metadata: {e})")
        else:
            lines.append("\n⚠ Install pydub for full audio features.")
        return "\n".join(lines)

    def _show_audio_info(self):
        messagebox.showinfo("Audio Info", self._audio_info_str())

    def _audio_trim(self):
        seg = self._load_audio()
        if seg is None: return
        dur = len(seg) / 1000
        d = tk.Toplevel(self); d.title("Trim Audio"); d.configure(bg=COLORS["bg"])
        tk.Label(d, text=f"Duration: {dur:.2f}s", bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(padx=20, pady=(12,4))
        s_var = tk.DoubleVar(value=0)
        e_var = tk.DoubleVar(value=dur)
        for label, var in [("Start (s):", s_var), ("End (s):", e_var)]:
            row = tk.Frame(d, bg=COLORS["bg"]); row.pack(padx=20, pady=4, fill="x")
            tk.Label(row, text=label, bg=COLORS["bg"], fg=COLORS["text"],
                     width=10, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg=COLORS["panel"], fg=COLORS["text"],
                     width=8, relief="flat").pack(side="left")
        def apply():
            trimmed = seg[int(s_var.get()*1000):int(e_var.get()*1000)]
            out = filedialog.asksaveasfilename(defaultextension=".wav",
                    filetypes=[("WAV","*.wav"),("MP3","*.mp3")])
            if out:
                trimmed.export(out); self._status.set(f"Trimmed → {out}")
            d.destroy()
        tk.Button(d, text="Trim & Save", command=apply, bg=COLORS["btn"],
                  fg="white", relief="flat", padx=14, pady=6).pack(pady=12)

    def _audio_volume(self):
        seg = self._load_audio()
        if seg is None: return
        d = tk.Toplevel(self); d.title("Change Volume"); d.configure(bg=COLORS["bg"])
        tk.Label(d, text="dB change (−20 to +20):", bg=COLORS["bg"],
                 fg=COLORS["text"], font=("Segoe UI", 10)).pack(padx=20, pady=(16,4))
        var = tk.DoubleVar(value=0)
        ttk.Scale(d, from_=-20, to=20, variable=var, orient="horizontal",
                  length=260).pack(padx=20)
        tk.Label(d, textvariable=var, bg=COLORS["bg"], fg=COLORS["highlight"]).pack()
        def apply():
            louder = seg + var.get()
            out = filedialog.asksaveasfilename(defaultextension=".wav",
                    filetypes=[("WAV","*.wav"),("MP3","*.mp3")])
            if out:
                louder.export(out); self._status.set(f"Saved → {out}")
            d.destroy()
        tk.Button(d, text="Apply & Save", command=apply, bg=COLORS["btn"],
                  fg="white", relief="flat", padx=14, pady=6).pack(pady=12)

    def _audio_reverse(self):
        seg = self._load_audio()
        if seg is None: return
        out = filedialog.asksaveasfilename(defaultextension=".wav",
                filetypes=[("WAV","*.wav"),("MP3","*.mp3")])
        if out:
            seg.reverse().export(out)
            self._status.set(f"Reversed → {out}")

    def _audio_export(self, fmt):
        seg = self._load_audio()
        if seg is None: return
        out = filedialog.asksaveasfilename(defaultextension=f".{fmt}",
                filetypes=[(fmt.upper(), f"*.{fmt}")])
        if out:
            seg.export(out, format=fmt)
            self._status.set(f"Exported → {out}")

    
    #  VIDEO TOOLS
    
    def _setup_video(self):
        info = self._video_info_str()
        self._show_text(info)

        self._section("🎞 Video Info")
        self._tool_btn("Show Info",          self._show_video_info)

        self._section("🖼 Extract")
        self._tool_btn("Extract Frame at …", self._video_extract_frame)
        self._tool_btn("Extract All Frames", self._video_extract_all)

        self._section("📊 Analysis")
        self._tool_btn("Show Histogram (frame)", self._video_histogram)

    def _video_info_str(self):
        size = os.path.getsize(self._path)
        lines = [f"File:      {os.path.basename(self._path)}",
                 f"Size:      {size:,} bytes  ({size/1024/1024:.2f} MB)"]
        if CV2_OK:
            cap = cv2.VideoCapture(self._path)
            fps   = cap.get(cv2.CAP_PROP_FPS)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            w     = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h     = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            dur   = total / fps if fps else 0
            cap.release()
            lines += [f"Resolution:{w} × {h}",
                      f"FPS:       {fps:.2f}",
                      f"Frames:    {total}",
                      f"Duration:  {dur:.2f} s  ({int(dur//60)}m {int(dur%60)}s)"]
        else:
            lines.append("\n⚠ Install opencv-python for video features.\n"
                         "  pip install opencv-python")
        return "\n".join(lines)

    def _show_video_info(self):
        messagebox.showinfo("Video Info", self._video_info_str())

    def _video_extract_frame(self):
        if not CV2_OK:
            messagebox.showerror("Missing", "pip install opencv-python"); return
        cap = cv2.VideoCapture(self._path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        d = tk.Toplevel(self); d.title("Extract Frame"); d.configure(bg=COLORS["bg"])
        tk.Label(d, text=f"Frame index (0 – {total-1}):", bg=COLORS["bg"],
                 fg=COLORS["text"], font=("Segoe UI", 10)).pack(padx=20, pady=(16,4))
        var = tk.IntVar(value=0)
        tk.Entry(d, textvariable=var, bg=COLORS["panel"], fg=COLORS["text"],
                 width=10, relief="flat").pack(padx=20)
        def extract():
            cap2 = cv2.VideoCapture(self._path)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, var.get())
            ret, frame = cap2.read(); cap2.release()
            if not ret:
                messagebox.showerror("Error", "Could not read frame."); return
            out = filedialog.asksaveasfilename(defaultextension=".png",
                    filetypes=[("PNG","*.png"),("JPEG","*.jpg")])
            if out:
                cv2.imwrite(out, frame)
                self._status.set(f"Frame saved → {out}")
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                self._show_image(img)
            d.destroy()
        tk.Button(d, text="Extract", command=extract, bg=COLORS["btn"],
                  fg="white", relief="flat", padx=14, pady=6).pack(pady=12)

    def _video_extract_all(self):
        if not CV2_OK:
            messagebox.showerror("Missing", "pip install opencv-python"); return
        out_dir = filedialog.askdirectory(title="Select output folder")
        if not out_dir: return
        def worker():
            cap = cv2.VideoCapture(self._path)
            i = 0
            while True:
                ret, frame = cap.read()
                if not ret: break
                cv2.imwrite(os.path.join(out_dir, f"frame_{i:05d}.png"), frame)
                i += 1
            cap.release()
            self._status.set(f"Extracted {i} frames → {out_dir}")
        threading.Thread(target=worker, daemon=True).start()
        self._status.set("Extracting frames … (background)")

    def _video_histogram(self):
        if not CV2_OK or not PIL_OK:
            messagebox.showerror("Missing", "pip install opencv-python pillow"); return
        cap = cv2.VideoCapture(self._path)
        ret, frame = cap.read(); cap.release()
        if not ret: return
        import io, matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(8, 3), facecolor="#1a1a2e")
        colors = ("b","g","r"); names=("Blue","Green","Red")
        for i,(c,n) in enumerate(zip(colors, names)):
            hist = cv2.calcHist([frame],[i],None,[256],[0,256])
            axes[i].plot(hist, color=c)
            axes[i].set_title(n, color="white")
            axes[i].set_facecolor("#16213e")
            axes[i].tick_params(colors="white")
        fig.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format="png"); buf.seek(0)
        plt.close(fig)
        img = Image.open(buf)
        self._show_image(img)

    
    #  TEXT TOOLS
    
    def _setup_text(self):
        with open(self._path, "r", errors="replace") as f:
            self._text_content = f.read()
        self._show_text(self._text_content)

        self._section("🔍 Analyse")
        self._tool_btn("Word / Line Count",  self._text_count)
        self._tool_btn("Character Frequency",self._text_char_freq)

        self._section("✏️  Edit")
        self._tool_btn("Find & Replace …",   self._text_find_replace)
        self._tool_btn("To UPPERCASE",       lambda: self._text_transform("upper"))
        self._tool_btn("To lowercase",       lambda: self._text_transform("lower"))
        self._tool_btn("Reverse Lines",      lambda: self._text_transform("rev_lines"))
        self._tool_btn("Sort Lines A→Z",     lambda: self._text_transform("sort"))
        self._tool_btn("Remove Blank Lines", lambda: self._text_transform("rm_blank"))

        self._section("💾 Export")
        self._tool_btn("Save As …",          self._text_save)

    def _show_text(self, content):
        self._preview_label.pack_forget()
        self._text_output.config(state="normal")
        self._text_output.delete("1.0", "end")
        self._text_output.insert("1.0", content)
        self._text_output.config(state="disabled")
        self._text_output.pack(fill="both", expand=True, padx=10, pady=10)

    def _text_count(self):
        txt = self._text_content
        lines = txt.splitlines()
        words = len(txt.split())
        chars = len(txt)
        messagebox.showinfo("Text Stats",
            f"Lines:      {len(lines)}\n"
            f"Words:      {words}\n"
            f"Characters: {chars}")

    def _text_char_freq(self):
        from collections import Counter
        freq = Counter(c for c in self._text_content if c.isalpha())
        top = freq.most_common(10)
        msg = "\n".join(f"  '{c}': {n}" for c,n in top)
        messagebox.showinfo("Top 10 Characters", msg)

    def _text_find_replace(self):
        d = tk.Toplevel(self); d.title("Find & Replace"); d.configure(bg=COLORS["bg"])
        for label in ("Find:", "Replace:"):
            tk.Label(d, text=label, bg=COLORS["bg"], fg=COLORS["text"],
                     font=("Segoe UI", 10)).pack(padx=20, pady=(12,0), anchor="w")
            e = tk.Entry(d, bg=COLORS["panel"], fg=COLORS["text"], width=36,
                         relief="flat", font=("Segoe UI", 10))
            e.pack(padx=20)
            if label == "Find:": find_e = e
            else:                repl_e = e
        def apply():
            self._text_content = self._text_content.replace(
                find_e.get(), repl_e.get())
            self._show_text(self._text_content)
            d.destroy()
        tk.Button(d, text="Replace All", command=apply, bg=COLORS["btn"],
                  fg="white", relief="flat", padx=14, pady=6).pack(pady=12)

    def _text_transform(self, op):
        t = self._text_content
        if op == "upper":     t = t.upper()
        elif op == "lower":   t = t.lower()
        elif op == "rev_lines": t = "\n".join(reversed(t.splitlines()))
        elif op == "sort":    t = "\n".join(sorted(t.splitlines()))
        elif op == "rm_blank":t = "\n".join(l for l in t.splitlines() if l.strip())
        self._text_content = t
        self._show_text(t)

    def _text_save(self):
        out = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file","*.txt"),("All","*.*")])
        if out:
            with open(out,"w") as f: f.write(self._text_content)
            self._status.set(f"Saved → {out}")

    
    #  UNKNOWN file
    
    def _setup_unknown(self):
        size = os.path.getsize(self._path)
        info = (f"File:      {os.path.basename(self._path)}\n"
                f"Size:      {size:,} bytes\n"
                f"Extension: {os.path.splitext(self._path)[1] or '(none)'}\n\n"
                f"This file type is not recognised.\n"
                f"Supported types:\n"
                f"  Images : jpg png bmp gif tiff webp ico\n"
                f"  Audio  : mp3 wav ogg flac aac m4a\n"
                f"  Video  : mp4 avi mov mkv wmv flv webm\n"
                f"  Text   : txt csv log json xml html md py …")
        self._show_text(info)
        self._section("ℹ File Info")
        self._tool_btn("Show File Info", lambda: messagebox.showinfo("Info", info))



if __name__ == "__main__":
    app = MultimediaApp()
    app.mainloop()
