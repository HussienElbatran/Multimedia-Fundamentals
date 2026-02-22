# 🎬 Multimedia Fundamentals Course

A comprehensive Python-based course on **Multimedia Processing**, covering image, audio, video, text,
and compression techniques — paired with an interactive Tkinter desktop application for hands-on exploration.

---

## 📁 Project Structure

```
Multimedia-Course/
│
├── 00_Multimedia_Tutorials.ipynb   # Overview & course index
├── 01_Introduction.ipynb           # Intro to multimedia concepts
├── 02_Image_Processing.ipynb       # Image manipulation with OpenCV & Pillow
├── 03_Audio_Processing.ipynb       # Audio analysis with Pydub
├── 04_Video_Processing.ipynb       # Video frame extraction with OpenCV
├── 05_Text_Processing.ipynb        # Text & NLP techniques
├── 06_Compression.ipynb            # Compression algorithms & formats
│
├── datasets/
│   ├── sample_image.jpg            # Sample image for exercises
│   ├── sample_audio.wav            # Sample audio clip
│   └── sample_video.mp4            # Sample video file
│
├── app.py                      # Main Tkinter multimedia app
└── requirements.txt            # Python dependencies

```

---

## Course Notebooks

| # | Notebook | Topics Covered |
|---|----------|----------------|
| 00 | Multimedia Tutorials | Course overview, setup guide |
| 01 | Introduction | What is multimedia? Types, formats, use cases |
| 02 | Image Processing | Read/write images, color spaces, filters, histograms |
| 03 | Audio Processing | Load audio, waveforms, effects, export |
| 04 | Video Processing | Frame extraction, playback, video properties |
| 05 | Text Processing | Tokenization, frequency analysis, NLP basics |
| 06 | Compression | Lossy vs lossless, formats, compression ratios |

---

## Multimedia Desktop App

An interactive **Tkinter** application that accepts any media file and automatically applies relevant processing tools based on file type.

### Features
- 🖼️ **Images** — view, resize, apply filters, histogram analysis
- 🎵 **Audio** — playback, waveform display, effects
- 🎬 **Video** — frame extraction, video info
- 📄 **Text/Other** — text analysis tools

### Run the App

```bash
python app.py
```

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- [FFmpeg](https://ffmpeg.org/download.html) (required for audio processing with Pydub — must be added to system `PATH`)

### Install Dependencies

```bash
pip install -r "requirements.txt"
```

**Dependencies:**

| Package | Purpose |
|---------|---------|
| `pillow` | Image manipulation |
| `opencv-python` | Video analysis & frame extraction |
| `numpy` | Numerical operations (required by OpenCV) |
| `matplotlib` | Histograms & plots |
| `pydub` | Audio manipulation |

---

## Getting Started

1. **Clone or download** this repository
2. **Install dependencies** (see above)
3. **Open any notebook** in Jupyter Lab/Notebook to follow the course
4. **Run the app** for interactive experimentation:
   ```bash
   python "app.py"
   ```

### Launch Jupyter

```bash
jupyter notebook
```

Then open the notebooks in order, starting with `00_Multimedia_Tutorials.ipynb`.

---

## Tools & Libraries

- [OpenCV](https://opencv.org/) — Computer vision & video processing
- [Pillow](https://python-pillow.org/) — Image processing
- [Pydub](https://github.com/jiaaro/pydub) — Audio manipulation
- [Matplotlib](https://matplotlib.org/) — Visualization
- [NumPy](https://numpy.org/) — Numerical computing
- [Tkinter](https://docs.python.org/3/library/tkinter.html) — GUI framework (built into Python)

---

## License

This course material is intended for educational purposes.
