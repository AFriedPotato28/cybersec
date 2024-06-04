import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Text
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
from pydub import AudioSegment
import imageio
import numpy as np
import os
import threading, time
import pyaudio


class SteganographyApp:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.geometry("520x520")
        self.root.title("Steganography Tool")

        self.audio_segment = None
        self.payload_audio_segment = None
        self.stream = None
        self.is_playing = False
        self.is_paused = False
        self.stop_flag = threading.Event()

        self.cover_file_path = ""
        self.stego_file_path = ""
        self.payload_file_path = ""
        self.video_file_path = None
        self.payload_video_file_path = None

        self.setup_gui()
        self.root.mainloop()

    def check_limit(self):
        if self.operation_combobox.get() == "Encode":
            cover_file_size = os.path.getsize(self.cover_file_path)
            payload_file_size = os.path.getsize(self.payload_file_path) 
            if cover_file_size < payload_file_size:
                messagebox.showerror("Error", "Payload file size is greater than cover file size.")
                return False
        return True
    


    def setup_gui(self):
        self.operation_label = tk.Label(self.root, text="Select Operation:")
        self.operation_label.place(x=120, y=10)

        self.operation_combobox = ttk.Combobox(self.root, values=["Encode", "Decode"])
        self.operation_combobox.place(x=220, y=10)
        self.operation_combobox.bind("<<ComboboxSelected>>", self.update_ui)

        self.cover_label = tk.Label(self.root, text="Cover Object: None", width=25)
        self.cover_drop = tk.Listbox(self.root, height=2, width=30, justify="center")
        self.cover_drop.insert(1, "Drag/Browser cover files here")
        self.cover_drop.itemconfig(0, {'fg':'blue'})
        self.cover_drop.drop_target_register(DND_FILES)
        self.cover_drop.dnd_bind('<<Drop>>', self.handle_cover_stego_drop)
        self.cover_drop.bind("<Double-Button-1>", self.browse_cover)

        self.payload_label = tk.Label(self.root, text="Payload Object: None", width=25)
        self.payload_drop = tk.Listbox(self.root, height=2, width=30, justify="center")
        self.payload_drop.insert(1, "Drag/Browser payload files here")
        self.payload_drop.itemconfig(0, {'fg':'blue'})
        self.payload_drop.drop_target_register(DND_FILES)
        self.payload_drop.dnd_bind('<<Drop>>', self.handle_payload_drop)
        self.payload_drop.bind("<Double-Button-1>", self.browse_payload)

        self.stego_label = tk.Label(self.root, text="Stego Object: None", width=25)
        self.stego_drop = tk.Listbox(self.root, height=2, width=30, justify="center")
        self.stego_drop.insert(1, "Drag/Browser stego files here")
        self.stego_drop.itemconfig(0, {'fg':'blue'})
        self.stego_drop.drop_target_register(DND_FILES)
        self.stego_drop.dnd_bind('<<Drop>>', self.handle_cover_stego_drop)
        self.stego_drop.bind("<Double-Button-1>", self.browse_stego)

        self.encode_button = tk.Button(self.root, text="Encode", command=self.encode)
        self.decode_button = tk.Button(self.root, text="Decode", command=self.decode)
        self.image_label = tk.Label(self.root)  # Label to display the original image
        self.payload_image_label = tk.Label(self.root) # Label to display the payload image
        self.encoded_image_label = tk.Label(self.root) # Label to display the encoded image

        self.lsb_label = tk.Label(self.root, text="Number of LSBs to use:")
        self.lsb_spinbox = tk.Spinbox(self.root, from_=1, to=8, width=5)

        self.payload_text = Text(self.root, height=10, width=23)

        self.play_button = tk.Button(self.root, text="Play", command=self.play_audio, width=5)
        self.pause_button = tk.Button(self.root, text="Pause", command=self.pause_audio, width=5)
        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_audio_or_video, width=5)

        self.play_button_payload = tk.Button(self.root, text="Play", command=self.play_payload_audio, width=5)
        self.pause_button_payload = tk.Button(self.root, text="Pause", command=self.pause_payload_audio, width=5)
        self.stop_button_payload = tk.Button(self.root, text="Stop", command=self.stop_payload_audio_or_video, width=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_ui(self, event):
        operation = self.operation_combobox.get()
        # Clear the image and text widgets when operation is changed
        self.image_label.config(image='', text='')
        self.payload_image_label.config(image='', text='')
        self.payload_text.delete('1.0', tk.END)

        if operation == "Encode":
            self.decode_button.place_forget()
            self.stego_label.place_forget()
            self.stego_drop.place_forget()
            self.reset_media_controls()
            self.cover_label.config(text="Cover Object: None")
            self.payload_label.config(text="Payload: None")

            self.cover_drop.place(x=50, y=240)
            self.cover_label.place(x=50, y=280)
            self.payload_drop.place(x=280, y=240)
            self.payload_label.place(x=280, y=280)
            self.lsb_label.place(x=120, y=320)
            self.lsb_spinbox.place(x=250, y=320)
            self.encode_button.place(x=320, y=315)
            self.payload_text.place(x=280, y=50)
            self.image_label.place(x=80, y=50)
            self.payload_image_label.place(x=280, y=50)

        elif operation == "Decode":
            self.payload_text.place_forget()
            self.cover_label.place_forget()
            self.cover_drop.place_forget()
            self.payload_drop.place_forget()
            self.payload_label.place_forget()
            self.encode_button.place_forget()
            self.reset_media_controls()
            self.stego_label.config(text="Stego Object: None")

            self.stego_drop.place(x=150, y=240)
            self.stego_label.place(x=150, y=280)
            self.lsb_label.place(x=120, y=310)
            self.lsb_spinbox.place(x=250, y=310)
            self.decode_button.place(x=320, y=305)

    def handle_cover_stego_drop(self, event):
        file_path = event.data.strip("{}")
        if self.operation_combobox.get() == "Encode":
            self.stop_audio_or_video()  # Stop existing audio or video stream
            self.cover_file_path = file_path
            if file_path.lower().endswith(('.png', '.bmp', '.gif')):
                self.display_image(file_path)
                self.cover_label.config(text=f"Cover Object: {os.path.basename(file_path)}")
                self.reset_media_controls()
                self.image_label.place(x=80, y=60)
            elif file_path.lower().endswith(('.mp3', '.wav')):
                self.image_label.place_forget()
                self.cover_label.config(text=f"Cover Object: {os.path.basename(file_path)}")
                self.load_audio(file_path)
                self.place_media_controls()
            elif file_path.lower().endswith('.mp4'):
                self.cover_label.config(text=f"Cover Object: {os.path.basename(file_path)}")
                self.video_file_path = file_path
                self.play_video(file_path)
                self.load_audio(file_path)
                self.place_media_controls()
                self.image_label.place(x=60, y=45)
            else:
                messagebox.showerror("Error", "Unsupported cover object type.")

        elif self.operation_combobox.get() == "Decode":
            self.stop_audio_or_video()  # Stop existing audio or video stream
            self.stego_file_path = file_path
            if file_path.lower().endswith(('.png', '.bmp', '.gif')):
                self.display_image(file_path)
                self.stego_label.config(text=f"Stego Object: {os.path.basename(file_path)}")
                self.reset_media_controls()
                self.image_label.place(x=175, y=80)
            elif file_path.lower().endswith(('.mp3', '.wav')):
                self.image_label.place_forget()
                self.stego_label.config(text=f"Stego Object: {os.path.basename(file_path)}")
                self.load_audio(file_path)
                self.place_decode_media_controls()
            elif file_path.lower().endswith('.mp4'):
                self.stego_label.config(text=f"Stego Object: {os.path.basename(file_path)}")
                self.video_file_path = file_path
                self.play_video(file_path)
                self.load_audio(file_path)
                self.place_decode_media_controls()
                self.image_label.place(x=160, y=40)
            else:
                messagebox.showerror("Error", "Unsupported stego object type.")

    def handle_payload_drop(self, event):
        file_path = event.data.strip("{}")
        self.payload_file_path = file_path
        if file_path.lower().endswith('.txt'):
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.display_payload_text(file_path)
        elif file_path.lower().endswith(('.png', '.bmp', '.gif')):
            self.payload_text.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.reset_media_controls()
            self.display_payload_image(file_path)
        elif file_path.lower().endswith(('.mp3', '.wav')):
            self.payload_text.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.load_payload_audio(file_path)
            self.place_payload_media_controls()
        elif file_path.lower().endswith('.mp4'):
            self.payload_text.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.payload_video_file_path = file_path
            self.play_payload_video(file_path)
            self.load_payload_audio(file_path)
            self.place_payload_media_controls()
        else:
            messagebox.showerror("Error", "Unsupported payload type.")
            

    def display_payload_text(self, file_path):
        try:
            with open(file_path, 'r') as file:
                payload_content = file.read()
                self.payload_text.delete('1.0', tk.END)
                self.payload_text.insert(tk.END, payload_content)
                self.payload_text.place(x=280, y=50)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read payload file: {e}")

    def display_image(self, file_path):
        try:
            image = Image.open(file_path)
            resized_image = image.resize((130, 130), Image.Resampling.LANCZOS)
            self.tk_image = ImageTk.PhotoImage(resized_image)
            self.image_label.config(image=self.tk_image)
            self.image_label.image = self.tk_image
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def display_payload_image(self, file_path):
        try:
            image = Image.open(file_path)
            resized_image = image.resize((130, 130), Image.Resampling.LANCZOS)
            self.tk_payload_image = ImageTk.PhotoImage(resized_image)
            self.payload_image_label.config(image=self.tk_payload_image)
            self.payload_image_label.image = self.tk_payload_image
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open image: {e}")

    def load_audio(self, file_path):
        try:
            self.audio_segment = AudioSegment.from_file(file_path)
            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio: {e}")

    def load_payload_audio(self, file_path):
        try:
            self.payload_audio_segment = AudioSegment.from_file(file_path)
            self.play_button_payload.config(state=tk.NORMAL)
            self.pause_button_payload.config(state=tk.NORMAL)
            self.stop_button_payload.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load payload audio: {e}")

    def place_decode_media_controls(self):
        self.play_button.place(x=160, y=210)
        self.pause_button.place(x=220, y=210)
        self.stop_button.place(x=280, y=210)

    def place_media_controls(self):
        self.play_button.place(x=60, y=210)
        self.pause_button.place(x=120, y=210)
        self.stop_button.place(x=180, y=210)

    def place_payload_media_controls(self):
        self.play_button_payload.place(x=300, y=210)
        self.pause_button_payload.place(x=360, y=210)
        self.stop_button_payload.place(x=420, y=210)

    def reset_media_controls(self):
        self.play_button.place_forget()
        self.pause_button.place_forget()
        self.stop_button.place_forget()
        self.play_button_payload.place_forget()
        self.pause_button_payload.place_forget()
        self.stop_button_payload.place_forget()

    def browse_cover(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("Image/Audio/Video Files", "*.png;*.bmp;*.gif;*.mp3;*.wav;*.mp4")])
        if file_path:
            self.cover_file_path = file_path
            self.handle_cover_stego_drop(type('event', (object,), {'data': file_path}))

    def browse_payload(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("Text/Audio/Video Files", "*.txt;*.mp3;*.wav;*.mp4;*.png;*.bmp;*.gif")])
        if file_path:
            self.payload_file_path = file_path
            self.handle_payload_drop(type('event', (object,), {'data': file_path}))

    def browse_stego(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("Image/Audio/Video Files", "*.png;*.bmp;*.gif;*.mp3;*.wav;*.mp4")])
        if file_path:
            self.stego_file_path = file_path
            self.handle_cover_stego_drop(type('event', (object,), {'data': file_path}))

    def play_audio(self):
        if self.is_paused:  
            self.is_paused = False
            self.stop_flag.clear()
        elif not self.is_playing:
            self.is_playing = True
            self.stop_flag.clear()
            threading.Thread(target=self._play_audio_thread).start()

    def play_payload_audio(self):
        if self.is_paused:  
            self.is_paused = False
            self.stop_flag.clear()
        elif not self.is_playing:
            self.is_playing = True
            self.stop_flag.clear()
            threading.Thread(target=self._play_payload_audio_thread).start()

    def pause_audio(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.config(text="Resume")
        else:
            self.pause_button.config(text="Pause")

    def pause_payload_audio(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button_payload.config(text="Resume")
        else:
            self.pause_button_payload.config(text="Pause")

    def stop_audio_or_video(self):
        if self.is_playing or self.is_paused:
            self.stop_flag.set()
            self.is_paused = False
            self.is_playing = False
            self.reset_media_controls()
            self.image_label.config(image='', text='')

    def stop_payload_audio_or_video(self):
        if self.is_playing or self.is_paused:
            self.stop_flag.set()
            self.is_paused = False
            self.is_playing = False
            self.reset_media_controls()
            self.payload_image_label.config(image='', text='')

    def _play_audio_thread(self):
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(self.audio_segment.sample_width),
                            channels=self.audio_segment.channels,
                            rate=self.audio_segment.frame_rate,
                            output=True)

            chunk_size = 1024
            audio_data = self.audio_segment.raw_data

            for i in range(0, len(audio_data), chunk_size):
                if self.stop_flag.is_set():
                    break
                if self.is_paused:
                    while self.is_paused and not self.stop_flag.is_set():
                        time.sleep(0.1)
                stream.write(audio_data[i:i + chunk_size])

            stream.stop_stream()
            stream.close()
            p.terminate()
        finally:
            self.is_playing = False

    def _play_payload_audio_thread(self):
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(self.payload_audio_segment.sample_width),
                            channels=self.payload_audio_segment.channels,
                            rate=self.payload_audio_segment.frame_rate,
                            output=True)

            chunk_size = 1024
            audio_data = self.payload_audio_segment.raw_data

            for i in range(0, len(audio_data), chunk_size):
                if self.stop_flag.is_set():
                    break
                if self.is_paused:
                    while self.is_paused and not self.stop_flag.is_set():
                        time.sleep(0.1)
                stream.write(audio_data[i:i + chunk_size])

            stream.stop_stream()
            stream.close()
            p.terminate()
        finally:
            self.is_playing = False

    def _play_video_stream(self, file_path):
        try:
            video = imageio.get_reader(file_path, 'ffmpeg')
            for frame in video:
                while not self.is_playing and not self.stop_flag.is_set():
                    time.sleep(0.1)  # Wait until 'Play' button is pressed
                if self.stop_flag.is_set():
                    break
                if self.is_paused:
                    while self.is_paused and not self.stop_flag.is_set():
                        time.sleep(0.1)  # Wait while paused
                frame_image = Image.fromarray(np.uint8(frame)).resize((160, 160), Image.Resampling.LANCZOS)
                self.tk_frame_image = ImageTk.PhotoImage(frame_image)
                self.image_label.config(image=self.tk_frame_image)
                self.image_label.image = self.tk_frame_image
                time.sleep(0.03)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {e}")

    def _play_payload_video_stream(self, file_path):
        try:
            video = imageio.get_reader(file_path, 'ffmpeg')
            for frame in video:
                while not self.is_playing and not self.stop_flag.is_set():
                    time.sleep(0.1)  # Wait until 'Play' button is pressed
                if self.stop_flag.is_set():
                    break
                if self.is_paused:
                    while self.is_paused and not self.stop_flag.is_set():
                        time.sleep(0.1)  # Wait while paused
                frame_image = Image.fromarray(np.uint8(frame)).resize((160, 160), Image.Resampling.LANCZOS)
                self.tk_frame_image = ImageTk.PhotoImage(frame_image)
                self.payload_image_label.config(image=self.tk_frame_image)
                self.payload_image_label.image = self.tk_frame_image
                time.sleep(0.03)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {e}")

    def play_video(self, file_path):
        self.is_playing = False
        self.is_paused = False
        self.stop_flag.clear()
        self.video_thread = threading.Thread(target=self._play_video_stream, args=(file_path,))
        self.video_thread.start()

    def play_payload_video(self, file_path):
        self.is_playing = False
        self.is_paused = False
        self.stop_flag.clear()
        self.payload_video_thread = threading.Thread(target=self._play_payload_video_stream, args=(file_path,))
        self.payload_video_thread.start()

    def on_closing(self):
        self.stop_audio_or_video()
        self.root.destroy()

    def encode(self):
        # Your encoding implementation here
        pass

    def decode(self):
        # Your decoding implementation here
        pass

SteganographyApp()
