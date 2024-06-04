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
import steganography

class SteganographyApp:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.geometry("520x520")
        self.root.title("Steganography Tool")

        self.cover_audio_segment = None
        self.payload_audio_segment = None
        self.cover_stream = None
        self.payload_stream = None
        self.cover_is_playing = False
        self.payload_is_playing = False
        self.cover_is_paused = False
        self.payload_is_paused = False
        self.cover_stop_flag = threading.Event()
        self.payload_stop_flag = threading.Event()

        self.cover_file_path = ""
        self.stego_file_path = ""
        self.payload_file_path = ""
        self.video_file_path = None
        self.payload_video_file_path = None

        self.setup_gui()
        self.root.mainloop()

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

        self.play_cover_button = tk.Button(self.root, text="Play", command=self.play_cover_audio, width=5)
        self.pause_cover_button = tk.Button(self.root, text="Pause", command=self.pause_cover_audio, width=5)
        self.stop_cover_button = tk.Button(self.root, text="Stop", command=self.stop_cover_audio_or_video, width=5)

        self.play_payload_button = tk.Button(self.root, text="Play", command=self.play_payload_audio, width=5)
        self.pause_payload_button = tk.Button(self.root, text="Pause", command=self.pause_payload_audio, width=5)
        self.stop_payload_button = tk.Button(self.root, text="Stop", command=self.stop_payload_audio_or_video, width=5)

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
            self.stop_cover_audio_or_video()  # Stop existing audio or video stream
            self.cover_file_path = file_path
            if file_path.lower().endswith(('.png', '.bmp', '.gif')):
                self.display_image(file_path)
                self.cover_label.config(text=f"Cover Object: {os.path.basename(file_path)}")
                self.reset_media_controls()
                self.image_label.place(x=80, y=60)
            elif file_path.lower().endswith(('.mp3', '.wav')):
                self.image_label.place_forget()
                self.cover_label.config(text=f"Cover Object: {os.path.basename(file_path)}")
                self.load_cover_audio(file_path)
                self.place_cover_media_controls()
            elif file_path.lower().endswith('.mp4'):
                self.cover_label.config(text=f"Cover Object: {os.path.basename(file_path)}")
                self.video_file_path = file_path
                self.play_cover_video(file_path)
                self.load_cover_audio(file_path)
                self.place_cover_media_controls()
                self.image_label.place(x=60, y=45)
            else:
                messagebox.showerror("Error", "Unsupported cover object type.")

        elif self.operation_combobox.get() == "Decode":
            self.stop_cover_audio_or_video()  # Stop existing audio or video stream
            self.stego_file_path = file_path
            if file_path.lower().endswith(('.png', '.bmp', '.gif')):
                self.display_image(file_path)
                self.stego_label.config(text=f"Stego Object: {os.path.basename(file_path)}")
                self.reset_media_controls()
                self.image_label.place(x=175, y=80)
            elif file_path.lower().endswith(('.mp3', '.wav')):
                self.image_label.place_forget()
                self.stego_label.config(text=f"Stego Object: {os.path.basename(file_path)}")
                self.load_cover_audio(file_path)
                self.place_decode_cover_media_controls()
            elif file_path.lower().endswith('.mp4'):
                self.stego_label.config(text=f"Stego Object: {os.path.basename(file_path)}")
                self.video_file_path = file_path
                self.play_cover_video(file_path)
                self.load_cover_audio(file_path)
                self.place_decode_cover_media_controls()
                self.image_label.place(x=160, y=40)
            else:
                messagebox.showerror("Error", "Unsupported stego object type.")

    def handle_payload_drop(self, event):
        file_path = event.data.strip("{}")
        self.stop_payload_audio_or_video()  # Stop existing audio or video stream
        self.payload_file_path = file_path
        if file_path.lower().endswith(('.png', '.bmp', '.gif')):
            self.payload_text.place_forget()
            self.display_payload_image(file_path)
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.reset_media_controls(is_cover=False)
            self.payload_image_label.place(x=280, y=70)
        elif file_path.lower().endswith(('.mp3', '.wav')):
            self.payload_text.place_forget()
            self.payload_image_label.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.load_payload_audio(file_path)
            self.place_payload_media_controls()
        elif file_path.lower().endswith('.txt'):
            with open(file_path, 'r') as file:
                text = file.read()
                self.payload_text.delete('1.0', tk.END)
                self.payload_text.insert(tk.END, text)
                self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.reset_media_controls(is_cover=False)
        elif file_path.lower().endswith('.mp4'):
            self.payload_text.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.payload_video_file_path = file_path
            self.play_payload_video(file_path)
            self.load_payload_audio(file_path)
            self.place_payload_media_controls()
            self.payload_image_label.place(x=280, y=55)
        else:
            messagebox.showerror("Error", "Unsupported payload object type.")

    def browse_cover(self, event=None):
        file_path = filedialog.askopenfilename(title="Select Cover Object", filetypes=[("All Files", "*.*")])
        if file_path:
            self.handle_cover_stego_drop(type('', (), {'data': file_path})())

    def browse_payload(self, event=None):
        file_path = filedialog.askopenfilename(title="Select Payload Object", filetypes=[("All Files", "*.*")])
        if file_path:
            self.handle_payload_drop(type('', (), {'data': file_path})())

    def browse_stego(self, event=None):
        file_path = filedialog.askopenfilename(title="Select Stego Object", filetypes=[("All Files", "*.*")])
        if file_path:
            self.handle_cover_stego_drop(type('', (), {'data': file_path})())

    def display_image(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((130, 130), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.image_label.config(image=image)
        self.image_label.image = image

    def display_payload_image(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((130, 130), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.payload_image_label.config(image=image)
        self.payload_image_label.image = image

    def reset_media_controls(self, is_cover=True):
        if is_cover:
            self.play_cover_button.place_forget()
            self.pause_cover_button.place_forget()
            self.stop_cover_button.place_forget()
        else:
            self.play_payload_button.place_forget()
            self.pause_payload_button.place_forget()
            self.stop_payload_button.place_forget()

    def place_cover_media_controls(self):
        self.play_cover_button.place(x=60, y=210)
        self.pause_cover_button.place(x=120, y=210)
        self.stop_cover_button.place(x=180, y=210)

    def place_decode_cover_media_controls(self):
        self.play_cover_button.place(x=160, y=210)
        self.pause_cover_button.place(x=220, y=210)
        self.stop_cover_button.place(x=280, y=210)

    def place_payload_media_controls(self):
        self.play_payload_button.place(x=300, y=210)
        self.pause_payload_button.place(x=360, y=210)
        self.stop_payload_button.place(x=420, y=210)

    def load_cover_audio(self, file_path):
        self.cover_audio_segment = AudioSegment.from_file(file_path)

    def load_payload_audio(self, file_path):
        self.payload_audio_segment = AudioSegment.from_file(file_path)

    def play_cover_audio(self):
        if self.cover_audio_segment:
            self.cover_stop_flag.clear()
            self.cover_is_playing = True
            threading.Thread(target=self._play_audio, args=(self.cover_audio_segment, self.cover_stop_flag, True)).start()

    def play_payload_audio(self):
        if self.payload_audio_segment:
            self.payload_stop_flag.clear()
            self.payload_is_playing = True
            threading.Thread(target=self._play_audio, args=(self.payload_audio_segment, self.payload_stop_flag, False)).start()

    def _play_audio(self, audio_segment, stop_flag, is_cover=True):
        chunk = 1024
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(audio_segment.sample_width),
                        channels=audio_segment.channels,
                        rate=audio_segment.frame_rate,
                        output=True)

        if is_cover:
            self.cover_stream = stream
        else:
            self.payload_stream = stream

        for chunk_data in audio_segment[::chunk]:
            if stop_flag.is_set():
                break
            stream.write(chunk_data._data)
            while self.cover_is_paused if is_cover else self.payload_is_paused:
                time.sleep(0.1)

        stream.stop_stream()
        stream.close()
        p.terminate()
        if is_cover:
            self.cover_is_playing = False
        else:
            self.payload_is_playing = False

    def pause_cover_audio(self):
        if self.cover_is_playing:
            self.cover_is_paused = not self.cover_is_paused
            if self.cover_is_paused:
                self.pause_cover_button.config(text="Resume")
            else:
                self.pause_cover_button.config(text="Pause")

    def pause_payload_audio(self):
        if self.payload_is_playing:
            self.payload_is_paused = not self.payload_is_paused
            if self.payload_is_paused:
                self.pause_payload_button.config(text="Resume")
            else:
                self.pause_payload_button.config(text="Pause")

    def stop_cover_audio_or_video(self):
        '''self.cover_stop_flag.set()
        self.cover_is_paused = False
        self.pause_cover_button.config(text="Pause")'''
        if self.cover_is_playing or self.cover_is_paused:
            self.cover_stop_flag.set()
            self.cover_is_paused = False
            self.cover_is_playing = False
            self.reset_media_controls(is_cover=True)
            self.image_label.config(image='', text='')

    def stop_payload_audio_or_video(self):
        '''self.payload_stop_flag.set()
        self.payload_is_paused = False
        self.pause_payload_button.config(text="Pause")'''
        if self.payload_is_playing or self.payload_is_paused:
            self.payload_stop_flag.set()
            self.payload_is_paused = False
            self.payload_is_playing = False
            self.reset_media_controls(is_cover=False)
            self.payload_image_label.config(image='', text='')

    def play_cover_video(self, file_path):
        video = imageio.get_reader(file_path)
        self.cover_is_playing = False
        self.cover_is_paused = False
        self.cover_stop_flag.clear()
        threading.Thread(target=self._play_video_stream, args=(file_path,)).start()

    def play_payload_video(self, file_path):
        video = imageio.get_reader(file_path)
        self.payload_is_playing = False
        self.payload_is_paused = False
        self.payload_stop_flag.clear()
        threading.Thread(target=self._play_payload_video_stream, args=(file_path,)).start()

    '''def _play_video(self, video, stop_flag, is_cover=True):
        for frame in video.iter_data():
            if stop_flag.is_set():
                break
            frame_image = Image.fromarray(frame)
            frame_image.thumbnail((160, 160), Image.LANCZOS)
            frame_image = ImageTk.PhotoImage(frame_image)
            if is_cover:
                self.image_label.config(image=frame_image)
                self.image_label.image = frame_image
            else:
                self.payload_image_label.config(image=frame_image)
                self.payload_image_label.image = frame_image
            time.sleep(1 / video.get_meta_data()['fps'])'''

    def _play_video_stream(self, file_path):
        try:
            video = imageio.get_reader(file_path, 'ffmpeg')
            for frame in video:
                while not self.cover_is_playing and not self.cover_stop_flag.is_set():
                    time.sleep(0.1)  # Wait until 'Play' button is pressed
                if self.cover_stop_flag.is_set():
                    break
                if self.cover_is_paused:
                    while self.cover_is_paused and not self.cover_stop_flag.is_set():
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
                while not self.payload_is_playing and not self.payload_stop_flag.is_set():
                    time.sleep(0.1)  # Wait until 'Play' button is pressed
                if self.payload_stop_flag.is_set():
                    break
                if self.payload_is_paused:
                    while self.payload_is_paused and not self.payload_stop_flag.is_set():
                        time.sleep(0.1)  # Wait while paused
                frame_image = Image.fromarray(np.uint8(frame)).resize((160, 160), Image.Resampling.LANCZOS)
                self.tk_frame_image = ImageTk.PhotoImage(frame_image)
                self.payload_image_label.config(image=self.tk_frame_image)
                self.payload_image_label.image = self.tk_frame_image
                time.sleep(0.03)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {e}")

    def encode(self):
        # Implement the encoding logic here
        cover_path = self.cover_file_path
        payload_path = self.payload_file_path
        bits = int(self.lsb_spinbox.get())
        output_path = filedialog.asksaveasfilename()

        if not cover_path or not payload_path:
            messagebox.showerror("Error", "Please select cover and payload objects.")
            return
        
        steganography.encode(cover_path,payload_path,bits,output_path)
        messagebox.showinfo("Success", "Encoding completed successfully.")

    def decode(self):
        # Implement the encoding logic here
        stego_path = self.stego_file_path
        bits = int(self.lsb_spinbox.get())
        output_path = filedialog.asksaveasfilename()

        if not stego_path:
            messagebox.showerror("Error", "Please select stego objects.")
            return
        
        data = steganography.decode(stego_path,bits)
        print(data)
        steganography.write_file(f"{output_path}.{data['message_extension']}", data["message"])
        messagebox.showinfo("Success", "Decoding completed successfully.")

    def on_closing(self):
        self.stop_cover_audio_or_video()
        self.stop_payload_audio_or_video()
        self.root.destroy()

if __name__ == "__main__":
    SteganographyApp()
