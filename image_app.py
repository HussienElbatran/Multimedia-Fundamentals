"""
image_app.py — Dedicated Image Manipulation App
Requires: pip install pillow matplotlib numpy
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, io, math

try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    MPL_OK = True
except ImportError:
    MPL_OK = False

# ── palette ───────────────────────────────────────────────────────────────────
C = {
    "bg":        "#0d0d1a",
    "panel":     "#13132b",
    "sidebar":   "#0f0f24",
    "card":      "#1a1a3e",
    "accent":    "#7c3aed",
    "accent2":   "#a78bfa",
    "highlight": "#f59e0b",
    "red":       "#ef4444",
    "green":     "#22c55e",
    "text":      "#f1f5f9",
    "subtext":   "#94a3b8",
    "border":    "#2e2e5e",
}

IMAGE_TYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp *.ico"),
    ("All files", "*.*"),
]


# ══════════════════════════════════════════════════════════════════════════════
class ImageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🖼️  Image Studio")
        self.geometry("1200x760")
        self.minsize(1000, 640)
        self.configure(bg=C["bg"])

        if not PIL_OK:
            messagebox.showerror(
                "Missing library",
                "Pillow is required.\n\nRun:  pip install pillow matplotlib numpy")
            self.destroy(); return

        # state
        self._original: Image.Image | None = None
        self._current:  Image.Image | None = None
        self._history:  list[Image.Image]  = []   # undo stack
        self._redo:     list[Image.Image]  = []
        self._zoom      = 1.0
        self._path      = ""

        self._status_var = tk.StringVar(value="Open an image to begin …")
        self._zoom_var   = tk.StringVar(value="100 %")

        self._build_ui()

    # ── root layout ───────────────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_canvas_area(body)
        self._build_statusbar()

    # ── header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=C["card"], pady=0)
        hdr.pack(fill="x")

        tk.Label(hdr, text="🖼️  Image Studio",
                 font=("Segoe UI", 17, "bold"),
                 bg=C["card"], fg=C["text"], padx=18, pady=10).pack(side="left")

        # quick toolbar
        for txt, cmd in [
            ("📂 Open",  self._open_file),
            ("💾 Save",  self._save_file),
            ("💾 Save As", self._save_as),
            ("↩ Undo",  self._undo),
            ("↪ Redo",  self._redo_op),
            ("⟳ Reset", self._reset),
        ]:
            self._hdr_btn(hdr, txt, cmd)

        # zoom controls
        tk.Label(hdr, text="Zoom:", bg=C["card"], fg=C["subtext"],
                 font=("Segoe UI", 9)).pack(side="right", padx=(0, 4))
        for sym, factor in [("−", 0.8), ("+", 1.25)]:
            b = tk.Button(hdr, text=sym, width=3,
                          command=lambda f=factor: self._zoom_by(f),
                          bg=C["accent"], fg="white", relief="flat",
                          font=("Segoe UI", 11, "bold"), cursor="hand2")
            b.pack(side="right", padx=2, pady=6)
        tk.Label(hdr, textvariable=self._zoom_var, bg=C["card"], fg=C["highlight"],
                 font=("Segoe UI", 9, "bold"), width=6).pack(side="right", padx=4)

    def _hdr_btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd,
                      bg=C["accent"], fg="white", relief="flat",
                      font=("Segoe UI", 9, "bold"), padx=10, pady=6,
                      cursor="hand2", activebackground=C["accent2"],
                      activeforeground="white", bd=0)
        b.pack(side="left", padx=3, pady=6)
        b.bind("<Enter>", lambda e: b.config(bg=C["accent2"]))
        b.bind("<Leave>", lambda e: b.config(bg=C["accent"]))

    # ── sidebar (tool panels) ─────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        outer = tk.Frame(parent, bg=C["sidebar"], width=230)
        outer.pack(side="left", fill="y")
        outer.pack_propagate(False)

        canvas = tk.Canvas(outer, bg=C["sidebar"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._tool_frame = tk.Frame(canvas, bg=C["sidebar"])
        win_id = canvas.create_window((0, 0), window=self._tool_frame, anchor="nw")

        def on_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        self._tool_frame.bind("<Configure>", on_cfg)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win_id, width=e.width))

        # mousewheel scroll on sidebar
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._populate_sidebar()

    def _populate_sidebar(self):
        tf = self._tool_frame

        def section(title, icon):
            tk.Frame(tf, bg=C["border"], height=1).pack(fill="x", pady=(10, 0))
            tk.Label(tf, text=f"{icon}  {title}", bg=C["sidebar"],
                     fg=C["highlight"], font=("Segoe UI", 9, "bold"),
                     anchor="w", padx=8).pack(fill="x")

        def btn(text, cmd, color=None):
            c = color or C["card"]
            b = tk.Button(tf, text=text, command=cmd, bg=c, fg=C["text"],
                          font=("Segoe UI", 9), relief="flat", anchor="w",
                          padx=12, pady=5, cursor="hand2",
                          activebackground=C["accent"],
                          activeforeground="white", bd=0)
            b.pack(fill="x", padx=8, pady=2)
            b.bind("<Enter>", lambda e: b.config(bg=C["accent"]))
            b.bind("<Leave>", lambda e: b.config(bg=c))

        # ── Rotate & Flip
        section("Rotate & Flip", "🔄")
        btn("Rotate 90° CW",    lambda: self._op(lambda i: i.rotate(-90, expand=True)))
        btn("Rotate 90° CCW",   lambda: self._op(lambda i: i.rotate( 90, expand=True)))
        btn("Rotate 180°",      lambda: self._op(lambda i: i.rotate(180)))
        btn("Custom Rotate …",  self._dlg_rotate)
        btn("Flip Horizontal",  lambda: self._op(ImageOps.mirror))
        btn("Flip Vertical",    lambda: self._op(ImageOps.flip))

        # ── Color Adjustments
        section("Color", "🎨")
        btn("Grayscale",        lambda: self._op(lambda i: i.convert("L").convert("RGB")))
        btn("Invert Colors",    lambda: self._op(lambda i: ImageOps.invert(i.convert("RGB"))))
        btn("Sepia",            lambda: self._op(self._apply_sepia))
        btn("Solarize",         lambda: self._op(lambda i: ImageOps.solarize(i.convert("RGB"))))
        btn("Posterize",        lambda: self._op(lambda i: ImageOps.posterize(i.convert("RGB"), 3)))
        btn("Auto Contrast",    lambda: self._op(lambda i: ImageOps.autocontrast(i)))
        btn("Equalize Hist",    lambda: self._op(lambda i: ImageOps.equalize(i.convert("RGB"))))
        btn("Brightness …",     lambda: self._dlg_enhance("Brightness", ImageEnhance.Brightness))
        btn("Contrast …",       lambda: self._dlg_enhance("Contrast",   ImageEnhance.Contrast))
        btn("Saturation …",     lambda: self._dlg_enhance("Saturation", ImageEnhance.Color))
        btn("Sharpness …",      lambda: self._dlg_enhance("Sharpness",  ImageEnhance.Sharpness))

        # ── Filters
        section("Filters", "✨")
        btn("Blur",             lambda: self._op(lambda i: i.filter(ImageFilter.GaussianBlur(2))))
        btn("Strong Blur",      lambda: self._op(lambda i: i.filter(ImageFilter.GaussianBlur(8))))
        btn("Sharpen",          lambda: self._op(lambda i: i.filter(ImageFilter.SHARPEN)))
        btn("Edge Detect",      lambda: self._op(lambda i: i.filter(ImageFilter.FIND_EDGES)))
        btn("Emboss",           lambda: self._op(lambda i: i.filter(ImageFilter.EMBOSS)))
        btn("Smooth",           lambda: self._op(lambda i: i.filter(ImageFilter.SMOOTH_MORE)))
        btn("Detail",           lambda: self._op(lambda i: i.filter(ImageFilter.DETAIL)))
        btn("Contour",          lambda: self._op(lambda i: i.filter(ImageFilter.CONTOUR)))
        btn("Min Filter",       lambda: self._op(lambda i: i.filter(ImageFilter.MinFilter(3))))
        btn("Max Filter",       lambda: self._op(lambda i: i.filter(ImageFilter.MaxFilter(3))))

        # ── Crop & Resize
        section("Crop & Resize", "✂️")
        btn("Resize …",         self._dlg_resize)
        btn("Crop …",           self._dlg_crop)
        btn("Square Crop (center)", lambda: self._op(self._square_crop))
        btn("Fit to 512×512",   lambda: self._op(lambda i: ImageOps.fit(i,(512,512))))
        btn("Fit to 1024×1024", lambda: self._op(lambda i: ImageOps.fit(i,(1024,1024))))

        # ── Draw & Annotate
        section("Draw / Annotate", "✏️")
        btn("Add Border …",     self._dlg_border)
        btn("Add Text …",       self._dlg_text)
        btn("Draw Grid …",      self._dlg_grid)

        # ── Pixel / Channel
        section("Channels", "🔬")
        btn("Red Channel only",   lambda: self._op(lambda i: self._channel(i, 0)))
        btn("Green Channel only", lambda: self._op(lambda i: self._channel(i, 1)))
        btn("Blue Channel only",  lambda: self._op(lambda i: self._channel(i, 2)))
        btn("Swap R ↔ B",         lambda: self._op(lambda i: Image.merge("RGB", i.convert("RGB").split()[::-1])))

        # ── Info & Analysis
        section("Info & Analysis", "📊")
        btn("File Info",        self._show_info)
        btn("Pixel Inspector",  self._show_pixel_inspector)
        btn("Show Histogram",   self._show_histogram)
        btn("Color Palette",    self._show_palette)

    # ── canvas (preview) area ─────────────────────────────────────────────────
    def _build_canvas_area(self, parent):
        frame = tk.Frame(parent, bg=C["bg"])
        frame.pack(side="left", fill="both", expand=True)

        self._canvas = tk.Canvas(frame, bg=C["bg"], highlightthickness=0,
                                 cursor="crosshair")
        self._canvas.pack(fill="both", expand=True)

        # bind mouse
        self._canvas.bind("<Motion>",    self._on_mouse_move)
        self._canvas.bind("<Button-4>",  lambda e: self._zoom_by(1.25))
        self._canvas.bind("<Button-5>",  lambda e: self._zoom_by(0.8))
        self._canvas.bind("<MouseWheel>",
            lambda e: self._zoom_by(1.25 if e.delta > 0 else 0.8))

        # placeholder text
        self._canvas.create_text(
            600, 340, text="📂  Open an image to begin",
            font=("Segoe UI", 18), fill=C["border"], tags="placeholder")

    # ── status bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C["card"], pady=3)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar, textvariable=self._status_var, bg=C["card"], fg=C["subtext"],
                 font=("Segoe UI", 9), anchor="w", padx=12).pack(side="left")
        self._pixel_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._pixel_var, bg=C["card"], fg=C["accent2"],
                 font=("Consolas", 9), anchor="e", padx=12).pack(side="right")

    # ── file operations ───────────────────────────────────────────────────────
    def _open_file(self):
        p = filedialog.askopenfilename(title="Open Image", filetypes=IMAGE_TYPES)
        if not p: return
        img = Image.open(p)
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")
        self._path = p
        self._original = img.copy()
        self._current  = img.copy()
        self._history.clear(); self._redo.clear()
        self._zoom = 1.0; self._zoom_var.set("100 %")
        self._status_var.set(
            f"{os.path.basename(p)}  •  {img.width}×{img.height}  •  {img.mode}")
        self._refresh_canvas()

    def _save_file(self):
        if not self._current:
            messagebox.showwarning("No image", "Open an image first."); return
        if not self._path:
            self._save_as(); return
        self._current.save(self._path)
        self._status_var.set(f"Saved → {self._path}")

    def _save_as(self):
        if not self._current:
            messagebox.showwarning("No image", "Open an image first."); return
        out = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG","*.png"),("JPEG","*.jpg *.jpeg"),
                       ("BMP","*.bmp"),("TIFF","*.tiff"),("All","*.*")])
        if out:
            self._current.convert("RGB").save(out)
            self._path = out
            self._status_var.set(f"Saved → {out}")

    # ── history helpers ───────────────────────────────────────────────────────
    def _push_history(self, img: Image.Image):
        self._history.append(img.copy())
        self._redo.clear()
        if len(self._history) > 50:
            self._history.pop(0)

    def _undo(self):
        if not self._history:
            self._status_var.set("Nothing to undo."); return
        self._redo.append(self._current.copy())
        self._current = self._history.pop()
        self._refresh_canvas()
        self._status_var.set("Undo")

    def _redo_op(self):
        if not self._redo:
            self._status_var.set("Nothing to redo."); return
        self._history.append(self._current.copy())
        self._current = self._redo.pop()
        self._refresh_canvas()
        self._status_var.set("Redo")

    def _reset(self):
        if self._original is None: return
        self._push_history(self._current)
        self._current = self._original.copy()
        self._refresh_canvas()
        self._status_var.set("Reset to original.")

    # ── generic operation runner ──────────────────────────────────────────────
    def _op(self, fn):
        if self._current is None:
            messagebox.showwarning("No image", "Open an image first."); return
        try:
            self._push_history(self._current)
            result = fn(self._current)
            if result is None: return          # fn modified in-place (unused)
            self._current = result.convert("RGB") if result.mode not in ("RGB","RGBA") else result
            self._refresh_canvas()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    # ── canvas refresh ────────────────────────────────────────────────────────
    def _refresh_canvas(self):
        if self._current is None: return
        self._canvas.delete("all")
        w = int(self._current.width  * self._zoom)
        h = int(self._current.height * self._zoom)
        disp = self._current.resize((max(1,w), max(1,h)), Image.LANCZOS)
        self._tk_img = ImageTk.PhotoImage(disp)
        cx = max(self._canvas.winfo_width()  // 2, w // 2)
        cy = max(self._canvas.winfo_height() // 2, h // 2)
        self._canvas.create_image(cx, cy, image=self._tk_img, anchor="center")
        self._img_canvas_offset = (cx - w//2, cy - h//2)

    def _zoom_by(self, factor):
        self._zoom = max(0.05, min(self._zoom * factor, 10.0))
        self._zoom_var.set(f"{int(self._zoom*100)} %")
        self._refresh_canvas()

    def _on_mouse_move(self, event):
        if self._current is None: return
        ox, oy = self._img_canvas_offset if hasattr(self, "_img_canvas_offset") else (0,0)
        px = int((event.x - ox) / self._zoom)
        py = int((event.y - oy) / self._zoom)
        if 0 <= px < self._current.width and 0 <= py < self._current.height:
            pixel = self._current.getpixel((px, py))
            if isinstance(pixel, int): pixel = (pixel, pixel, pixel)
            r,g,b = pixel[:3]
            self._pixel_var.set(f"({px}, {py})  R:{r} G:{g} B:{b}  #{r:02x}{g:02x}{b:02x}")
        else:
            self._pixel_var.set("")

    # ── image operations ──────────────────────────────────────────────────────
    def _apply_sepia(self, img):
        gray = img.convert("L")
        return Image.merge("RGB", [
            gray.point(lambda p: min(int(p * 1.08), 255)),
            gray.point(lambda p: min(int(p * 0.84), 255)),
            gray.point(lambda p: min(int(p * 0.66), 255)),
        ])

    def _channel(self, img, ch):
        r = img.convert("RGB")
        channels = list(r.split())
        for i in range(3):
            if i != ch:
                channels[i] = channels[i].point(lambda _: 0)
        return Image.merge("RGB", channels)

    def _square_crop(self, img):
        s = min(img.size)
        left = (img.width  - s) // 2
        top  = (img.height - s) // 2
        return img.crop((left, top, left+s, top+s))

    # ── dialogs ───────────────────────────────────────────────────────────────
    def _dlg_rotate(self):
        self._simple_dialog(
            "Custom Rotate", "Angle (degrees):", 0.0, -360, 360,
            lambda v: self._op(lambda i: i.rotate(v, expand=True, fillcolor=0)))

    def _dlg_enhance(self, name, Enhancer):
        d = tk.Toplevel(self); d.title(name); d.configure(bg=C["bg"])
        d.resizable(False, False); d.grab_set()
        var = tk.DoubleVar(value=1.0)
        tk.Label(d, text=f"Factor  (0.1 → 3.0)", bg=C["bg"], fg=C["text"],
                 font=("Segoe UI", 10)).pack(padx=24, pady=(18, 6))
        frame = tk.Frame(d, bg=C["bg"]); frame.pack(padx=24, fill="x")
        scale = ttk.Scale(frame, from_=0.1, to=3.0, variable=var,
                          orient="horizontal", length=280)
        scale.pack(side="left")
        lbl = tk.Label(frame, textvariable=var, bg=C["bg"], fg=C["highlight"],
                       font=("Consolas", 10), width=5)
        lbl.pack(side="left", padx=6)
        var.trace_add("write", lambda *_: lbl.config(
            text=f"{var.get():.2f}"))
        def apply():
            self._op(lambda i: Enhancer(i).enhance(var.get()))
            d.destroy()
        tk.Button(d, text="Apply", command=apply, bg=C["accent"], fg="white",
                  relief="flat", padx=20, pady=7,
                  font=("Segoe UI", 10, "bold")).pack(pady=14)

    def _dlg_resize(self):
        if self._current is None: return
        d = tk.Toplevel(self); d.title("Resize"); d.configure(bg=C["bg"])
        d.resizable(False, False); d.grab_set()
        w_var = tk.IntVar(value=self._current.width)
        h_var = tk.IntVar(value=self._current.height)
        keep  = tk.BooleanVar(value=True)
        orig_w, orig_h = self._current.width, self._current.height
        for label, var in [("Width (px):", w_var), ("Height (px):", h_var)]:
            row = tk.Frame(d, bg=C["bg"]); row.pack(padx=24, pady=4, fill="x")
            tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                     width=14, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg=C["panel"], fg=C["text"],
                     width=8, relief="flat", font=("Consolas", 10)).pack(side="left")
        def sync_h(*_):
            if keep.get() and orig_w:
                h_var.set(int(w_var.get() * orig_h / orig_w))
        w_var.trace_add("write", sync_h)
        tk.Checkbutton(d, text="Keep aspect ratio", variable=keep,
                       bg=C["bg"], fg=C["text"], selectcolor=C["panel"],
                       activebackground=C["bg"]).pack(padx=24, anchor="w")
        def apply():
            self._op(lambda i: i.resize((max(1,w_var.get()), max(1,h_var.get())),
                                         Image.LANCZOS))
            d.destroy()
        tk.Button(d, text="Resize", command=apply, bg=C["accent"], fg="white",
                  relief="flat", padx=20, pady=7).pack(pady=14)

    def _dlg_crop(self):
        if self._current is None: return
        d = tk.Toplevel(self); d.title("Crop"); d.configure(bg=C["bg"])
        d.resizable(False, False); d.grab_set()
        W, H = self._current.width, self._current.height
        tk.Label(d, text=f"Image: {W} × {H}  px", bg=C["bg"], fg=C["subtext"],
                 font=("Segoe UI", 9)).pack(padx=24, pady=(12, 4))
        vars_ = {}
        for label, default in [("Left:", 0),("Top:", 0),("Right:", W),("Bottom:", H)]:
            row = tk.Frame(d, bg=C["bg"]); row.pack(padx=24, pady=3, fill="x")
            tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                     width=8, anchor="w").pack(side="left")
            v = tk.IntVar(value=default)
            tk.Entry(row, textvariable=v, bg=C["panel"], fg=C["text"],
                     width=8, relief="flat").pack(side="left")
            vars_[label] = v
        def apply():
            box = (vars_["Left:"].get(), vars_["Top:"].get(),
                   vars_["Right:"].get(), vars_["Bottom:"].get())
            self._op(lambda i: i.crop(box))
            d.destroy()
        tk.Button(d, text="Crop", command=apply, bg=C["accent"], fg="white",
                  relief="flat", padx=20, pady=7).pack(pady=14)

    def _dlg_border(self):
        self._simple_dialog(
            "Add Border", "Border size (px):", 20, 1, 200,
            lambda v: self._op(
                lambda i: ImageOps.expand(i, border=int(v), fill=(0,0,0))))

    def _dlg_text(self):
        if self._current is None: return
        d = tk.Toplevel(self); d.title("Add Text"); d.configure(bg=C["bg"])
        d.resizable(False, False); d.grab_set()
        vars_ = {}
        for label, default in [("Text:", "Hello!"), ("X:", 10), ("Y:", 10),
                                ("Font size:", 36), ("Color (hex):", "#ffffff")]:
            row = tk.Frame(d, bg=C["bg"]); row.pack(padx=24, pady=4, fill="x")
            tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                     width=14, anchor="w").pack(side="left")
            v = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=v, bg=C["panel"], fg=C["text"],
                     width=18, relief="flat").pack(side="left")
            vars_[label] = v
        def apply():
            def draw(img):
                out = img.copy().convert("RGBA")
                overlay = Image.new("RGBA", out.size, (0,0,0,0))
                draw_ctx = ImageDraw.Draw(overlay)
                try:
                    color = vars_["Color (hex):"].get()
                    size  = int(vars_["Font size:"].get())
                    draw_ctx.text(
                        (int(vars_["X:"].get()), int(vars_["Y:"].get())),
                        vars_["Text:"].get(), fill=color,
                        font=ImageFont.load_default(size=size))
                except Exception:
                    draw_ctx.text(
                        (int(vars_["X:"].get()), int(vars_["Y:"].get())),
                        vars_["Text:"].get(), fill=vars_["Color (hex):"].get())
                return Image.alpha_composite(out, overlay).convert("RGB")
            self._op(draw); d.destroy()
        tk.Button(d, text="Draw Text", command=apply, bg=C["accent"], fg="white",
                  relief="flat", padx=20, pady=7).pack(pady=14)

    def _dlg_grid(self):
        if self._current is None: return
        d = tk.Toplevel(self); d.title("Draw Grid"); d.configure(bg=C["bg"])
        d.resizable(False, False); d.grab_set()
        rows_v = tk.IntVar(value=4); cols_v = tk.IntVar(value=4)
        for label, var in [("Rows:",  rows_v), ("Columns:", cols_v)]:
            row = tk.Frame(d, bg=C["bg"]); row.pack(padx=24, pady=4, fill="x")
            tk.Label(row, text=label, bg=C["bg"], fg=C["text"],
                     width=10, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg=C["panel"], fg=C["text"],
                     width=6, relief="flat").pack(side="left")
        def apply():
            def draw(img):
                out = img.copy().convert("RGB")
                draw_ctx = ImageDraw.Draw(out)
                W, H = out.size
                for r in range(1, rows_v.get()):
                    y = r * H // rows_v.get()
                    draw_ctx.line([(0,y),(W,y)], fill="#ff0000", width=2)
                for c in range(1, cols_v.get()):
                    x = c * W // cols_v.get()
                    draw_ctx.line([(x,0),(x,H)], fill="#ff0000", width=2)
                return out
            self._op(draw); d.destroy()
        tk.Button(d, text="Draw Grid", command=apply, bg=C["accent"], fg="white",
                  relief="flat", padx=20, pady=7).pack(pady=14)

    def _simple_dialog(self, title, label, default, lo, hi, apply_fn):
        d = tk.Toplevel(self); d.title(title); d.configure(bg=C["bg"])
        d.resizable(False, False); d.grab_set()
        var = tk.DoubleVar(value=default)
        tk.Label(d, text=label, bg=C["bg"], fg=C["text"],
                 font=("Segoe UI", 10)).pack(padx=24, pady=(18,6))
        row = tk.Frame(d, bg=C["bg"]); row.pack(padx=24, fill="x")
        ttk.Scale(row, from_=lo, to=hi, variable=var,
                  orient="horizontal", length=260).pack(side="left")
        tk.Label(row, textvariable=var, bg=C["bg"], fg=C["highlight"],
                 font=("Consolas", 10), width=6).pack(side="left", padx=6)
        def apply():
            apply_fn(var.get()); d.destroy()
        tk.Button(d, text="Apply", command=apply, bg=C["accent"], fg="white",
                  relief="flat", padx=20, pady=7).pack(pady=14)

    # ── info & analysis ───────────────────────────────────────────────────────
    def _show_info(self):
        if self._current is None: return
        size = os.path.getsize(self._path) if self._path and os.path.exists(self._path) else 0
        orig = self._original
        info = (
            f"File:      {os.path.basename(self._path) if self._path else '(unsaved)'}\n"
            f"Disk size: {size:,} bytes  ({size/1024:.1f} KB)\n\n"
            f"Original:  {orig.width} × {orig.height} px\n"
            f"Current:   {self._current.width} × {self._current.height} px\n"
            f"Mode:      {self._current.mode}\n"
            f"Format:    {getattr(orig, 'format', 'N/A')}\n\n"
            f"Undo stack: {len(self._history)} step(s)\n"
            f"Zoom:      {int(self._zoom*100)} %"
        )
        messagebox.showinfo("Image Info", info)

    def _show_pixel_inspector(self):
        if self._current is None: return
        img = self._current.convert("RGB")
        W, H = img.size
        sample = 5
        d = tk.Toplevel(self); d.title("Pixel Grid Inspector"); d.configure(bg=C["bg"])
        d.geometry("480x480"); d.grab_set()

        cv = tk.Canvas(d, bg=C["bg"], highlightthickness=0)
        cv.pack(fill="both", expand=True)

        zoom_v = tk.IntVar(value=sample)

        def draw_grid(sz):
            cv.delete("all")
            patch = img.resize((sz*20, sz*20), Image.NEAREST)
            import io as _io
            buf = _io.BytesIO(); patch.save(buf, format="PNG"); buf.seek(0)
            tk_img = ImageTk.PhotoImage(Image.open(buf))
            cv._ref = tk_img
            cv.create_image(0, 0, image=tk_img, anchor="nw")
            step = patch.width // sz
            for r in range(sz):
                for c in range(sz):
                    x0, y0 = c*step, r*step
                    px = img.getpixel((min(c, W-1), min(r, H-1)))
                    if isinstance(px, int): px=(px,px,px)
                    bright = (px[0]*299 + px[1]*587 + px[2]*114) // 1000
                    fg = "black" if bright > 128 else "white"
                    cv.create_text(x0+step//2, y0+step//2,
                                   text=f"{px[0]}\n{px[1]}\n{px[2]}",
                                   fill=fg, font=("Consolas", 7))

        bar = tk.Frame(d, bg=C["bg"]); bar.pack(fill="x")
        tk.Label(bar, text="Sample size:", bg=C["bg"], fg=C["text"]).pack(side="left",padx=8)
        ttk.Scale(bar, from_=3, to=20, variable=zoom_v, orient="horizontal",
                  length=160, command=lambda _: draw_grid(zoom_v.get())).pack(side="left")
        draw_grid(sample)

    def _show_histogram(self):
        if not MPL_OK:
            messagebox.showerror("Missing", "pip install matplotlib numpy"); return
        img = self._current.convert("RGB")
        arr = np.array(img)
        fig, ax = plt.subplots(figsize=(6, 3), facecolor="#0d0d1a")
        ax.set_facecolor("#13132b")
        for i, (color, label) in enumerate(
                zip(["#ef4444","#22c55e","#3b82f6"], ["Red","Green","Blue"])):
            ax.hist(arr[:,:,i].ravel(), bins=256, color=color,
                    alpha=0.7, label=label, histtype="stepfilled")
        ax.legend(facecolor="#1a1a3e", edgecolor="none", labelcolor="white")
        ax.tick_params(colors=C["subtext"]); ax.set_xlim(0, 255)
        for spine in ax.spines.values(): spine.set_color(C["border"])
        fig.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format="png"); buf.seek(0); plt.close(fig)
        histo_img = Image.open(buf)
        # show in a new window
        d = tk.Toplevel(self); d.title("RGB Histogram"); d.configure(bg=C["bg"])
        tk_img = ImageTk.PhotoImage(histo_img)
        lbl = tk.Label(d, image=tk_img, bg=C["bg"]); lbl.pack()
        lbl._ref = tk_img

    def _show_palette(self):
        if self._current is None: return
        img = self._current.convert("RGB")
        colors = img.getcolors(maxcolors=img.width * img.height)
        if colors:
            colors.sort(key=lambda x: -x[0])
            top = colors[:16]
        else:
            top = []
        d = tk.Toplevel(self); d.title("Top Colors"); d.configure(bg=C["bg"])
        tk.Label(d, text="Most Common Colors (top 16)", bg=C["bg"], fg=C["text"],
                 font=("Segoe UI", 11, "bold")).pack(pady=(14,6))
        grid = tk.Frame(d, bg=C["bg"]); grid.pack(padx=16, pady=8)
        for idx, (count, (r,g,b)) in enumerate(top):
            col = idx % 8; row = idx // 8
            hex_ = f"#{r:02x}{g:02x}{b:02x}"
            bright = (r*299 + g*587 + b*114) // 1000
            fg = "black" if bright > 128 else "white"
            tk.Label(grid, bg=hex_, fg=fg, text=hex_,
                     font=("Consolas", 8), width=9, height=3,
                     relief="flat").grid(row=row, column=col, padx=3, pady=3)
        tk.Button(d, text="Close", command=d.destroy, bg=C["accent"], fg="white",
                  relief="flat", padx=14, pady=5).pack(pady=10)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ImageApp()
    app.mainloop()
