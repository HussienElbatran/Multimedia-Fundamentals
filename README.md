# 🎬 Multimedia Fundamentals Course

A complete **Python-based multimedia course** focused on teaching the fundamentals of **image, audio, video, text processing, and compression**.
The project combines structured Jupyter notebooks with a modular **Tkinter desktop application** that enables real-time experimentation with multimedia files.

---

## 📁 Project Structure

```
Multimedia-Course/
│
├── 00_Multimedia_Tutorials.ipynb
├── 01_Introduction.ipynb
├── 02_Image_Processing.ipynb
├── 03_Audio_Processing.ipynb
├── 04_Video_Processing.ipynb
├── 05_Text_Processing.ipynb
├── 06_Compression.ipynb
│
├── datasets/
│   ├── sample_image.jpg
│   ├── sample_audio.wav
│   └── sample_video.mp4
│
├── app.py
├── image_app.py
└── requirements.txt
```

---

## Course Overview

The notebooks provide step-by-step explanations and practical examples covering:

* Multimedia fundamentals
* Image processing techniques
* Audio manipulation
* Video analysis
* Text processing basics
* Compression concepts

Each notebook builds on the previous one to create a complete learning path.

---

## Multimedia Desktop Application

The desktop application automatically detects file types and provides the appropriate tools through a modular interface.

### 🖼️ Image Tools

* Image preview
* Resize and transformations
* Filters and color adjustments
* Histogram analysis
* Undo / redo workflow
* Dedicated Image Studio (`image_app.py`)

### 🎵 Audio Tools

* Audio playback
* Waveform visualization
* Basic audio effects
* Export processed audio

### 🎬 Video Tools

* Frame extraction
* Video metadata display
* Preview capabilities

### 📄 Text Tools

* Tokenization
* Frequency analysis
* Basic NLP utilities

---

## Run the Application

```
python app.py
```

---

## Setup & Installation

### Requirements

* Python 3.8+
* FFmpeg (required for audio processing)

### Install Dependencies

```
pip install -r requirements.txt
```

### Main Libraries

* Pillow
* OpenCV
* NumPy
* Matplotlib
* Pydub
* Tkinter

---

## Getting Started

1. Clone or download the repository
2. Install dependencies
3. Launch Jupyter and follow notebooks in order
4. Run the desktop application to practice

Launch Jupyter:

```
jupyter notebook
```

---

## Architecture Notes

* Modular design — each media type lives in its own module
* `app.py` acts as the entry point
* `image_app.py` demonstrates feature-level GUI isolation
* Easy to extend with AI or advanced processing modules

---

## Screenshots

### Main Multimedia App

![Main App](screenshots/main_app.png)

### Image Studio

![Image Studio](screenshots/image_studio.png)

---

## Learning Outcomes

After completing this course, you will be able to:

* Understand multimedia formats and workflows
* Process images, audio, video, and text using Python
* Build GUI tools for multimedia pipelines
* Visualize multimedia data
* Understand compression strategies
* Structure modular multimedia applications

---

## Notes

* Designed for education and experimentation
* Suitable for computer science students and beginners in multimedia processing
* Can be extended into a full multimedia editor

---

## License

This project is intended for educational use.
