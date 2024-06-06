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
        self.root.geometry("1080x720")
        self.root.title("Steganography Tool")

        self.cover_audio_segment = None
        self.payload_audio_segment = None
        self.encoded_audio_segment = None
        self.decoded_audio_segment = None
        self.cover_stream = None
        self.payload_stream = None
        self.encoded_stream = None
        self.decoded_steam = None
        self.cover_is_playing = False
        self.payload_is_playing = False
        self.encoded_is_playing = False
        self.decoded_is_playing = False
        self.cover_is_paused = False
        self.payload_is_paused = False
        self.encoded_is_paused = False
        self.decoded_is_paused = False
        self.cover_stop_flag = threading.Event()
        self.encoded_stop_flag = threading.Event()
        self.payload_stop_flag = threading.Event()
        self.decoded_stop_flag = threading.Event()

        self.cover_file_path = ""
        self.stego_file_path = ""
        self.payload_file_path = ""
        self.encoded_file_path = ""
        self.video_file_path = None
        self.payload_video_file_path = None

        self.encoded_label = tk.Label(self.root)
        self.encoded_image_label = tk.Label(self.root)

        self.setup_gui()
        self.root.mainloop()

    def setup_gui(self):
        self.operation_label = tk.Label(self.root, text="Select Operation:")
        self.operation_label.place(x=320, y=10)

        self.operation_combobox = ttk.Combobox(
            self.root, values=["Encode", "Decode", "Comparison"]
        )
        self.operation_combobox.place(x=420, y=10)
        self.operation_combobox.bind("<<ComboboxSelected>>", self.update_ui)

        self.cover_label = tk.Label(self.root, text="Cover Object: None", width=25)
        self.cover_drop = tk.Listbox(self.root, height=2, width=50, justify="center")
        self.cover_drop.insert(1, "Drag/Browser cover files here")
        self.cover_drop.itemconfig(0, {"fg": "blue"})
        self.cover_drop.drop_target_register(DND_FILES)
        self.cover_drop.dnd_bind("<<Drop>>", self.handle_cover_stego_drop)
        self.cover_drop.bind("<Double-Button-1>", self.browse_cover)

        self.payload_label = tk.Label(self.root, text="Payload Object: None", width=25)
        self.payload_drop = tk.Listbox(self.root, height=2, width=50, justify="center")
        self.payload_drop.insert(1, "Drag/Browser payload files here")
        self.payload_drop.itemconfig(0, {"fg": "blue"})
        self.payload_drop.drop_target_register(DND_FILES)
        self.payload_drop.dnd_bind("<<Drop>>", self.handle_payload_drop)
        self.payload_drop.bind("<Double-Button-1>", self.browse_payload)

        self.stego_label = tk.Label(self.root, text="Stego Object: None", width=25)
        self.stego_drop = tk.Listbox(self.root, height=2, width=50, justify="center")
        self.stego_drop.insert(1, "Drag/Browser stego files here")
        self.stego_drop.itemconfig(0, {"fg": "blue"})
        self.stego_drop.drop_target_register(DND_FILES)
        self.stego_drop.dnd_bind("<<Drop>>", self.handle_cover_stego_drop)
        self.stego_drop.bind("<Double-Button-1>", self.browse_stego)

        self.image1_label = tk.Label(self.root, text="Image 1 Object: None", width=25)
        self.image1_drop = tk.Listbox(self.root, height=2, width=50, justify="center")
        self.image1_drop.insert(1, "Drag/Browser Image files here")
        self.image1_drop.itemconfig(0, {"fg": "blue"})
        self.image1_drop.drop_target_register(DND_FILES)
        self.image1_drop.dnd_bind("<<Drop>>", self.handle_cover_stego_drop)
        self.image1_drop.bind("<Double-Button-1>", self.browse_image1)

        self.image2_label = tk.Label(self.root, text="Image 2 Object: None", width=25)
        self.image2_drop = tk.Listbox(self.root, height=2, width=50, justify="center")
        self.image2_drop.insert(1, "Drag/Browser Image files here")
        self.image2_drop.itemconfig(0, {"fg": "blue"})
        self.image2_drop.drop_target_register(DND_FILES)
        self.image2_drop.dnd_bind("<<Drop>>", self.handle_image2_drop)
        self.image2_drop.bind("<Double-Button-1>", self.browse_image2)

        self.encode_button = tk.Button(self.root, text="Encode", command=self.encode)
        self.compare_button = tk.Button(self.root, text="Compare", command=self.compare)
        self.decode_button = tk.Button(self.root, text="Decode", command=self.decode)
        self.image_label = tk.Label(self.root)  # Label to display the original image
        self.payload_image_label = tk.Label(
            self.root
        )  # Label to display the payload image
        self.encoded_label = tk.Label(self.root, text="Encoded file:")
        self.encoded_image_label = tk.Label(
            self.root
        )  # Label to display the encoded image

        self.image1_pic_label = tk.Label(self.root)  # Label to display image1
        self.image2_pic_label = tk.Label(self.root)  # Label to display image2
        self.image3_pic_label = tk.Label(self.root)  # Label to display image2

        self.lsb_label = tk.Label(self.root, text="Number of LSBs to use:")
        self.lsb_spinbox = tk.Spinbox(self.root, from_=1, to=8, width=5)

        self.decoded_text = Text(self.root, height=10, width=23)
        self.cover_text = Text(self.root, height=10, width=23)
        self.payload_text = Text(self.root, height=10, width=23)
        self.stego_text = Text(self.root, height=10, width=23)
        self.decodefile_label = tk.Label(self.root)

        self.play_cover_button = tk.Button(
            self.root, text="Play", command=self.play_cover_audio, width=5
        )
        self.pause_cover_button = tk.Button(
            self.root, text="Pause", command=self.pause_cover_audio, width=5
        )
        self.stop_cover_button = tk.Button(
            self.root, text="Stop", command=self.stop_cover_audio_or_video, width=5
        )

        self.play_decoded_button = tk.Button(
            self.root, text="Play", command=self.play_decoded_audio, width=5
        )
        self.stop_decoded_button = tk.Button(
            self.root, text="Play", command=self.stop_decoded_audio_or_video, width=5
        )

        self.play_payload_button = tk.Button(
            self.root, text="Play", command=self.play_payload_audio, width=5
        )
        self.pause_payload_button = tk.Button(
            self.root, text="Pause", command=self.pause_payload_audio, width=5
        )
        self.stop_payload_button = tk.Button(
            self.root, text="Stop", command=self.stop_payload_audio_or_video, width=5
        )

        self.play_encoded_button = tk.Button(
            self.root, text="Play", command=self.play_encoded_audio, width=5
        )
        self.pause_encoded_button = tk.Button(
            self.root, text="Pause", command=self.pause_encoded_audio, width=5
        )
        self.stop_encoded_button = tk.Button(
            self.root, text="Stop", command=self.stop_encoded_audio_or_video, width=5
        )

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_ui(self, event):
        operation = self.operation_combobox.get()
        # Clear the image and text widgets when operation is changed
        # self.image_label.config(image='', text='')
        # self.payload_image_label.config(image='', text='')
        # self.payload_text.delete('1.0', tk.END)

        if operation == "Encode":
            self.decode_button.place_forget()
            self.stego_label.place_forget()
            self.stego_drop.place_forget()
            self.cover_text.place_forget()
            self.payload_text.place_forget()
            self.reset_media_controls()
            self.image1_label.place_forget()
            self.image2_label.place_forget()
            self.image1_drop.place_forget()
            self.image2_drop.place_forget()
            self.image1_pic_label.place_forget()
            self.image2_pic_label.place_forget()
            self.image3_pic_label.place_forget()
            self.compare_button.place_forget()
            self.reset_media_controls()
            self.encoded_label.place_forget()
            self.stego_text.place_forget()
            self.decoded_text.place_forget()
            self.decodefile_label.place_forget()
            self.payload_image_label.place_forget()
            self.image_label.place_forget()
            self.image_label.config(image="")
            self.payload_image_label.config(image="")

            self.cover_label.config(text="Cover Object: None")
            self.payload_label.config(text="Payload: None")
            self.encoded_label.config(text="Encoded File: None")

            self.cover_drop.place(x=80, y=240)
            self.cover_label.place(x=140, y=280)
            self.payload_drop.place(x=500, y=240)
            self.payload_label.place(x=560, y=280)
            self.lsb_label.place(x=370, y=320)
            self.lsb_spinbox.place(x=500, y=320)
            self.encode_button.place(x=420, y=350)
            # self.payload_text.place(x=500, y=50)
            self.image_label.place(x=80, y=50)
            self.payload_image_label.place(x=500, y=50)

        elif operation == "Decode":
            self.decoded_text.place_forget()
            self.cover_text.place_forget()
            self.payload_text.place_forget()
            self.stego_text.place_forget()
            self.cover_label.place_forget()
            self.cover_drop.place_forget()
            self.payload_drop.place_forget()
            self.payload_label.place_forget()
            self.encode_button.place_forget()
            self.encoded_image_label.place_forget()
            self.image1_label.place_forget()
            self.image2_label.place_forget()
            self.image1_drop.place_forget()
            self.image2_drop.place_forget()
            self.compare_button.place_forget()
            self.payload_text.place_forget()
            self.image1_pic_label.place_forget()
            self.image2_pic_label.place_forget()
            self.image3_pic_label.place_forget()
            self.image_label.place_forget()
            self.payload_text.place_forget()
            self.payload_image_label.place_forget()
            self.reset_media_controls()
            self.encoded_label.place_forget()
            self.image_label.config(image="")
            self.payload_image_label.config(image="")

            self.stego_label.config(text="Stego Object: None")

            self.stego_drop.place(x=300, y=240)
            self.stego_label.place(x=355, y=280)
            self.lsb_label.place(x=360, y=310)
            self.lsb_spinbox.place(x=490, y=310)
            self.decode_button.place(x=420, y=340)

        elif operation == "Comparison":
            self.stego_drop.place_forget()
            self.stego_label.place_forget()
            self.lsb_label.place_forget()
            self.lsb_spinbox.place_forget()
            self.decode_button.place_forget()
            self.encode_button.place_forget()
            self.cover_label.place_forget()
            self.cover_drop.place_forget()
            self.payload_drop.place_forget()
            self.payload_label.place_forget()
            self.payload_image_label.place_forget()
            self.image_label.place_forget()
            self.payload_text.place_forget()
            self.reset_media_controls()
            self.decoded_text.place_forget()
            self.encoded_image_label.place_forget()
            self.decodefile_label.place_forget()
            self.image_label.config(image="")
            self.payload_image_label.config(image="")

            self.image1_drop.place(x=80, y=240)
            self.image1_label.place(x=140, y=280)
            self.image2_drop.place(x=500, y=240)
            self.image2_label.place(x=560, y=280)
            self.compare_button.place(x=420, y=315)
            self.image1_pic_label.place(x=80, y=50)
            self.image2_pic_label.place(x=500, y=50)
            self.image3_pic_label.place(x=180, y=360)

    def handle_cover_stego_drop(self, event):
        self.cover_text.place_forget()
        file_path = event.data.strip("{}")
        if self.operation_combobox.get() == "Encode":
            self.stop_cover_audio_or_video()  # Stop existing audio or video stream
            self.cover_file_path = file_path
            if file_path.lower().endswith((".png", ".bmp", ".gif")):
                self.display_image(file_path)
                self.cover_label.config(
                    text=f"Cover Object: {os.path.basename(file_path)}"
                )
                self.reset_media_controls()
                self.image_label.place(x=80, y=60)
            elif file_path.lower().endswith((".mp3", ".wav")):
                self.image_label.place_forget()
                self.cover_label.config(
                    text=f"Cover Object: {os.path.basename(file_path)}"
                )
                self.load_cover_audio(file_path)
                self.place_cover_media_controls()
            elif file_path.lower().endswith(".txt"):
                self.cover_text.place_forget()
                self.image_label.place_forget()
                self.display_cover_text(file_path)
                self.reset_media_controls(is_cover=False)
                self.cover_label.config(
                    text=f"Cover Object: {os.path.basename(file_path)}"
                )
            elif file_path.lower().endswith((".mp4", "avi")):
                self.cover_label.config(
                    text=f"Cover Object: {os.path.basename(file_path)}"
                )
                self.video_file_path = file_path
                self.play_cover_button.place(x=140, y=213)
                self.pause_cover_button.place(x=210, y=213)
                self.stop_cover_button.place(x=280, y=213)
                self.play_cover_video(file_path)
                self.load_cover_audio(file_path)
                self.image_label.place(x=60, y=45)
            else:
                messagebox.showerror("Error", "Unsupported cover object type.")

        elif self.operation_combobox.get() == "Decode":
            self.stop_cover_audio_or_video()  # Stop existing audio or video stream
            self.stego_file_path = file_path
            if file_path.lower().endswith((".png", ".bmp", ".gif")):
                self.display_image(file_path)
                self.stego_label.config(
                    text=f"Stego Object: {os.path.basename(file_path)}"
                )
                self.stego_text.place_forget()
                self.reset_media_controls()
                self.image_label.place(x=300, y=70)
            elif file_path.lower().endswith((".mp3", ".wav")):
                self.image_label.place_forget()
                self.stego_text.place_forget()
                self.stego_label.config(
                    text=f"Stego Object: {os.path.basename(file_path)}"
                )
                self.load_cover_audio(file_path)
                self.place_decode_cover_media_controls()
            elif file_path.lower().endswith(".txt"):
                self.image_label.place_forget()
                self.stego_text.place(x=300, y=80)
                self.display_stego_text(file_path)
                self.stego_label.config(
                    text=f"Stego Object: {os.path.basename(file_path)}"
                )
                self.reset_media_controls(is_cover=False)
            elif file_path.lower().endswith((".mp4", ".avi")):
                self.stego_label.config(
                    text=f"Stego Object: {os.path.basename(file_path)}"
                )
                self.stego_text.place_forget()
                self.video_file_path = file_path
                self.play_cover_video(file_path)
                self.load_cover_audio(file_path)
                self.place_decode_cover_media_controls()
                self.image_label.place(x=300, y=40)
            else:
                messagebox.showerror("Error", "Unsupported stego object type.")
        elif self.operation_combobox.get() == "Compare":
            self.stego_file_path = file_path
            if file_path.lower().endswith((".png", ".bmp", ".gif")):
                self.display_image(file_path)
                self.stego_label.config(
                    text=f"Stego Object: {os.path.basename(file_path)}"
                )
            else:
                messagebox.showerror("Error", "Unsupported stego object type.")

        elif self.operation_combobox.get() == "Comparison":
            self.image1_file_path = file_path
            if file_path.lower().endswith((".png", ".bmp", ".gif")):
                self.display_image1(file_path)
                self.image1_label.config(
                    text=f"Image 1 Object: {os.path.basename(file_path)}"
                )
                self.image1_pic_label.place(x=80, y=60)

    def handle_image2_drop(self, event):
        file_path = event.data.strip("{}")
        self.image2_file_path = file_path
        if file_path.lower().endswith((".png", ".bmp", ".gif")):
            self.display_image2(file_path)
            self.image2_label.config(
                text=f"Image 2 Object: {os.path.basename(file_path)}"
            )
            self.image2_pic_label.place(x=500, y=60)
        else:
            messagebox.showerror("Error", "Unsupported payload object type.")

    def handle_payload_drop(self, event):
        self.payload_text.place_forget()
        file_path = event.data.strip("{}")
        self.stop_payload_audio_or_video()  # Stop existing audio or video stream
        self.payload_file_path = file_path
        if file_path.lower().endswith((".png", ".gif")):
            self.payload_text.place_forget()
            self.display_payload_image(file_path)
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.reset_media_controls(is_cover=False)
            self.payload_image_label.place(x=500, y=60)
        elif file_path.lower().endswith((".mp3", ".wav")):
            self.payload_text.place_forget()
            self.payload_image_label.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.load_payload_audio(file_path)
            self.place_payload_media_controls()
        elif file_path.lower().endswith(".txt"):
            self.payload_text.place_forget()
            self.display_payload_text(file_path)
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.reset_media_controls(is_cover=False)
        elif file_path.lower().endswith((".mp4", ".avi")):
            self.payload_text.place_forget()
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")
            self.payload_video_file_path = file_path
            self.play_payload_button.place(x=560, y=213)
            self.pause_payload_button.place(x=630, y=213)
            self.stop_payload_button.place(x=700, y=213)
            self.play_payload_video(file_path)
            self.load_payload_audio(file_path)
            self.payload_image_label.place(x=500, y=40)
        else:
            # messagebox.showerror("Error", "Unsupported payload object type.")
            self.payload_text.place_forget()
            self.payload_image_label.place_forget()
            self.reset_media_controls(is_cover=False)
            self.payload_label.config(text=f"Payload: {os.path.basename(file_path)}")

    def display_payload_text(self, file_path):
        try:
            with open(file_path, "r") as file:
                payload_content = file.read()
                self.payload_text.delete("1.0", tk.END)
                self.payload_text.insert(tk.END, payload_content)
                self.payload_text.place(x=500, y=50, width=300)
                self.payload_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read payload file: {e}")

    def display_stego_text(self, file_path):
        try:
            with open(file_path, "r") as file:
                stego_content = file.read()
                self.stego_text.delete("1.0", tk.END)
                self.stego_text.insert(tk.END, stego_content)
                self.stego_text.place(x=300, y=60, width=300)
                self.stego_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read payload file: {e}")

    def display_cover_text(self, file_path):
        try:
            with open(file_path, "r") as file:
                cover_content = file.read()
                self.cover_text.delete("1.0", tk.END)
                self.cover_text.insert(tk.END, cover_content)
                self.cover_text.place(x=80, y=50, width=300)
                self.cover_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read payload file: {e}")

    def display_decoded_text(self, file_path):
        try:
            with open(file_path, "r") as file:
                cover_content = file.read()
                self.decoded_text.delete("1.0", tk.END)
                self.decoded_text.insert(tk.END, cover_content)
                self.decoded_text.place(x=300, y=400, width=300)
                self.decoded_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read payload file: {e}")

    def browse_cover(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Cover Object", filetypes=[("All Files", "*.*")]
        )
        if file_path:
            self.handle_cover_stego_drop(type("", (), {"data": file_path})())

    def browse_payload(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Payload Object", filetypes=[("All Files", "*.*")]
        )
        if file_path:
            self.handle_payload_drop(type("", (), {"data": file_path})())

    def browse_stego(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Stego Object", filetypes=[("All Files", "*.*")]
        )
        if file_path:
            self.handle_cover_stego_drop(type("", (), {"data": file_path})())

    def browse_image1(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Image Object", filetypes=[("All Files", "*.*")]
        )
        if file_path:
            self.handle_cover_stego_drop(type("", (), {"data": file_path})())

    def browse_image2(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select Image Object", filetypes=[("All Files", "*.*")]
        )
        if file_path:
            self.handle_image2_drop(type("", (), {"data": file_path})())

    def display_image(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((300, 150), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.image_label.config(image=image)
        self.image_label.image = image

    def display_image1(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((300, 150), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.image1_pic_label.config(image=image)
        self.image1_pic_label.image = image

    def display_image2(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((300, 150), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.image2_pic_label.config(image=image)
        self.image2_pic_label.image = image

    def display_compare(self, file_path):
        image = Image.open(file_path)
        resize_image = image.resize((520, 300))
        image = ImageTk.PhotoImage(resize_image)
        self.image3_pic_label.config(image=image)
        self.image3_pic_label.image = image

    def display_payload_image(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((300, 150), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.payload_image_label.config(image=image)
        self.payload_image_label.image = image

    def display_encoded_image(self, file_path):
        self.play_encoded_button.place_forget()
        self.stop_encoded_button.place_forget()
        self.encoded_label.place(x=200, y=350)
        self.encoded_label.update()
        self.root.update_idletasks()
        image = Image.open(file_path)
        image.thumbnail((300, 150), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.encoded_image_label.config(image=image)
        self.encoded_image_label.image = image
        self.encoded_image_label.place(x=200, y=400)

    def display_decoded_image(self, file_path):
        image = Image.open(file_path)
        image.thumbnail((300, 150), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        self.encoded_image_label.config(image=image)
        self.encoded_image_label.image = image
        self.encoded_image_label.place(x=300, y=400)

    def reset_media_controls(self, is_cover=True):
        if is_cover:
            self.play_cover_button.place_forget()
            self.pause_cover_button.place_forget()
            self.stop_cover_button.place_forget()
        else:
            self.play_payload_button.place_forget()
            self.pause_payload_button.place_forget()
            self.stop_payload_button.place_forget()
            self.play_encoded_button.place_forget()
            self.stop_encoded_button.place_forget()
            self.play_cover_button.place_forget()
            self.pause_cover_button.place_forget()
            self.stop_cover_button.place_forget()
            self.play_encoded_button.place_forget()
            self.stop_encoded_button.place_forget()

    def place_cover_media_controls(self):
        self.play_cover_button.place(x=140, y=135)
        self.pause_cover_button.place(x=210, y=135)
        self.stop_cover_button.place(x=280, y=135)

    def place_decode_cover_media_controls(self):
        self.play_cover_button.place(x=360, y=210)
        self.pause_cover_button.place(x=430, y=210)
        self.stop_cover_button.place(x=500, y=210)

    def place_decoded_media_controls(self):
        self.play_decoded_button.place(x=350, y=380)
        self.stop_decoded_button.place(x=400, y=380)

    def place_encoded_media_controls(self):
        self.encoded_label.place(x=160, y=350)
        self.play_encoded_button.place(x=180, y=390)
        self.stop_encoded_button.place(x=240, y=390)

    def place_payload_media_controls(self):
        self.play_payload_button.place(x=560, y=135)
        self.pause_payload_button.place(x=630, y=135)
        self.stop_payload_button.place(x=700, y=135)

    def load_cover_audio(self, file_path):
        self.cover_audio_segment = AudioSegment.from_file(file_path)

    def load_payload_audio(self, file_path):
        self.payload_audio_segment = AudioSegment.from_file(file_path)

    def load_encoded_audio(self, file_path):
        try:
            self.encoded_audio_segment = AudioSegment.from_file(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load encoded audio: {e}")

    def load_decoded_audio(self, file_path):
        try:
            self.decoded_audio_segment = AudioSegment.from_file(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load encoded audio: {e}")

    def play_cover_audio(self):
        if self.cover_audio_segment:
            self.cover_stop_flag.clear()
            self.cover_is_playing = True
            threading.Thread(
                target=self._play_audio,
                args=(self.cover_audio_segment, self.cover_stop_flag, True),
            ).start()

    def play_encoded_audio(self):
        if self.encoded_audio_segment:
            self.encoded_stop_flag.clear()
            self.encoded_is_playing = True
            threading.Thread(
                target=self._play_audio,
                args=(self.encoded_audio_segment, self.encoded_stop_flag, False),
            ).start()
        else:
            messagebox.showerror("Error", "No encoded audio loaded.")

    def play_decoded_audio(self):
        if self.decoded_audio_segment:
            self.decoded_stop_flag.clear()
            self.decoded_is_playing = True
            threading.Thread(
                target=self._play_audio,
                args=(self.decoded_audio_segment, self.decoded_stop_flag, False),
            ).start()
        else:
            messagebox.showerror("Error", "No encoded audio loaded.")

    def play_payload_audio(self):
        if self.payload_audio_segment:
            self.payload_stop_flag.clear()
            self.payload_is_playing = True
            threading.Thread(
                target=self._play_audio,
                args=(self.payload_audio_segment, self.payload_stop_flag, False),
            ).start()

    def _play_audio(self, audio_segment, stop_flag, is_cover=True):
        chunk = 1024
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(audio_segment.sample_width),
            channels=audio_segment.channels,
            rate=audio_segment.frame_rate,
            output=True,
        )

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

    def pause_encoded_audio(self):
        print("Pause button clicked")
        print(f"encoded_is_playing: {self.encoded_is_playing}")
        print(f"encoded_is_paused: {self.encoded_is_paused}")
        if self.encoded_is_playing:
            self.encoded_is_paused = not self.encoded_is_paused
            self.encoded_is_playing = False
            if self.encoded_is_paused:
                self.pause_encoded_button.config(text="Resume")
            else:
                self.pause_encoded_button.config(text="Pause")
        print(f"encoded_is_playing: {self.encoded_is_playing}")
        print(f"encoded_is_paused: {self.encoded_is_paused}")

    def pause_payload_audio(self):
        if self.payload_is_playing:
            self.payload_is_paused = not self.payload_is_paused
            if self.payload_is_paused:
                self.pause_payload_button.config(text="Resume")
            else:
                self.pause_payload_button.config(text="Pause")

    def stop_cover_audio_or_video(self):
        """self.cover_stop_flag.set()
        self.cover_is_paused = False
        self.pause_cover_button.config(text="Pause")"""
        if self.cover_is_playing or self.cover_is_paused:
            self.cover_stop_flag.set()
            self.cover_is_paused = False
            self.cover_is_playing = False
            self.reset_media_controls(is_cover=True)
            self.image_label.config(image="", text="")

    def stop_encoded_audio_or_video(self):
        """self.cover_stop_flag.set()
        self.cover_is_paused = False
        self.pause_cover_button.config(text="Pause")"""
        if self.encoded_is_playing or self.encoded_is_paused:
            self.encoded_stop_flag.set()
            self.encoded_is_paused = False
            self.encoded_is_playing = False
            self.reset_media_controls(is_cover=True)
            self.image_label.config(image="", text="")

    def stop_decoded_audio_or_video(self):
        """self.cover_stop_flag.set()
        self.cover_is_paused = False
        self.pause_cover_button.config(text="Pause")"""
        if self.decoded_is_playing or self.decoded_is_paused:
            self.decoded_stop_flag.set()
            self.decoded_is_paused = False
            self.decoded_is_playing = False
            self.reset_media_controls(is_cover=True)
            self.image_label.config(image="", text="")

    def stop_payload_audio_or_video(self):
        """self.payload_stop_flag.set()
        self.payload_is_paused = False
        self.pause_payload_button.config(text="Pause")"""
        if self.payload_is_playing or self.payload_is_paused:
            self.payload_stop_flag.set()
            self.payload_is_paused = False
            self.payload_is_playing = False
            self.reset_media_controls(is_cover=False)
            self.payload_image_label.config(image="", text="")

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
        threading.Thread(
            target=self._play_payload_video_stream, args=(file_path,)
        ).start()

    """def _play_video(self, video, stop_flag, is_cover=True):
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
            time.sleep(1 / video.get_meta_data()['fps'])"""

    def _play_video_stream(self, file_path):
        try:
            video = imageio.get_reader(file_path, "ffmpeg")
            for frame in video:
                while not self.cover_is_playing and not self.cover_stop_flag.is_set():
                    time.sleep(0.1)  # Wait until 'Play' button is pressed
                if self.cover_stop_flag.is_set():
                    break
                if self.cover_is_paused:
                    while self.cover_is_paused and not self.cover_stop_flag.is_set():
                        time.sleep(0.1)  # Wait while paused
                frame_image = Image.fromarray(np.uint8(frame)).resize(
                    (300, 160), Image.Resampling.LANCZOS
                )
                self.tk_frame_image = ImageTk.PhotoImage(frame_image)
                self.image_label.config(image=self.tk_frame_image)
                self.image_label.image = self.tk_frame_image
                time.sleep(0.03)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {e}")

    def _play_payload_video_stream(self, file_path):
        try:
            video = imageio.get_reader(file_path, "ffmpeg")
            for frame in video:
                while (
                    not self.payload_is_playing and not self.payload_stop_flag.is_set()
                ):
                    time.sleep(0.1)  # Wait until 'Play' button is pressed
                if self.payload_stop_flag.is_set():
                    break
                if self.payload_is_paused:
                    while (
                        self.payload_is_paused and not self.payload_stop_flag.is_set()
                    ):
                        time.sleep(0.1)  # Wait while paused
                frame_image = Image.fromarray(np.uint8(frame)).resize(
                    (300, 160), Image.Resampling.LANCZOS
                )
                self.tk_frame_image = ImageTk.PhotoImage(frame_image)
                self.payload_image_label.config(image=self.tk_frame_image)
                self.payload_image_label.image = self.tk_frame_image
                time.sleep(0.03)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play video: {e}")

    def encode(self):
        # Implement the encoding logic here
        cover_path = self.cover_file_path
        cover_path_extension = cover_path.lower().split(".")[-1]
        payload_path = self.payload_file_path
        bits = int(self.lsb_spinbox.get())
        output_path = filedialog.asksaveasfilename() + f".{cover_path_extension}"

        if not cover_path or not payload_path:
            messagebox.showerror("Error", "Please select cover and payload objects.")
            return

        try:
            steganography.encode(cover_path, payload_path, bits, output_path)
            messagebox.showinfo("Success", "Encoding completed successfully.")
            if cover_path_extension in ["png", "bmp"]:
                self.encoded_label.config(
                    text=f"Encoded file: {os.path.basename(output_path)}"
                )
                self.display_encoded_image(output_path)
                self.root.update_idletasks()
            if cover_path_extension in ["wav"]:
                self.encoded_label.config(
                    text=f"Encoded file: {os.path.basename(output_path)}"
                )
                self.load_encoded_audio(output_path)
                self.place_encoded_media_controls()
                self.root.update_idletasks()
            if cover_path_extension in ["avi"]:
                self.encoded_label.config(
                    text=f"Encoded file: {os.path.basename(output_path)}"
                )
                self.video_file_path = output_path
                self.play_cover_button.place(x=140, y=213)
                self.pause_cover_button.place(x=210, y=213)
                self.stop_cover_button.place(x=280, y=213)
                self.play_cover_video(output_path)
                self.load_cover_audio(output_path)
                self.image_label.place(x=200, y=350)
            if cover_path_extension in ["txt"]:
                self.cover_label.config(
                    text=f"Encoded file: {os.path.basename(output_path)}"
                )
                self.encoded_image_label.place_forget()
                self.decoded_text.place(x=200, y=350)
                with open(output_path, "r") as file:
                    cover_content = file.read()
                    self.decoded_text.delete("1.0", tk.END)
                    self.decoded_text.insert(tk.END, cover_content)
                    self.decoded_text.place(x=300, y=400, width=300)
                    self.decoded_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to encode: {str(e)}")

    def decode(self):
        # Implement the encoding logic here
        stego_path = self.stego_file_path
        bits = int(self.lsb_spinbox.get())
        output_path = filedialog.asksaveasfilename()

        if not stego_path:
            messagebox.showerror("Error", "Please select stego objects.")
            return

        data = steganography.decode(stego_path, bits)
        print(data)

        steganography.write_file(
            f"{output_path}.{data['message_extension']}", data["message"]
        )
        messagebox.showinfo("Success", "Decoding completed successfully.")
        print("hit" + data["message_extension"])
        if data["message_extension"] in ["txt"]:
            self.decodefile_label.place(x=300, y=370)
            self.decodefile_label.config(
                text=f"Decoded file: {os.path.basename(output_path)}" + ".txt"
            )
            file_to_read = output_path + "." + data["message_extension"]
            print("file to read: " + file_to_read)
            self.display_decoded_text(file_to_read)
        elif data["message_extension"] in ["png", "bmp"]:
            self.decodefile_label.place(x=300, y=370)
            self.decodefile_label.config(
                text=f"Decoded file: {os.path.basename(output_path)}"
                + "."
                + data["message_extension"]
            )
            file_to_read = output_path + "." + data["message_extension"]
            self.display_decoded_image(file_to_read)
            self.root.update_idletasks()
        elif data["message_extension"] in ["wav"]:
            self.decodefile_label.place(x=300, y=370)
            self.encoded_label.config(
                text=f"Decoded file: {os.path.basename(output_path)}"
                + "."
                + data["message_extension"]
            )
            file_to_read = output_path + "." + data["message_extension"]
            self.load_decoded_audio(file_to_read)
            self.place_decoded_media_controls()
            self.root.update_idletasks()
        else:
            self.decodefile_label.place(x=300, y=370)
            self.decodefile_label.config(
                text=f"Decoded file: {os.path.basename(output_path)}"
                + "."
                + data["message_extension"]
            )

    def compare(self):
        image1_path = self.image1_file_path
        print(image1_path)
        image2_path = self.image2_file_path
        print(image2_path)
        output_path = filedialog.asksaveasfilename() + ".png"
        try:
            steganography.compare_object(image1_path, image2_path, output_path)
            self.display_compare(output_path)
            print(output_path)
        except Exception as error:
            messagebox.showerror("Error", f"{str(error)}")

    def on_closing(self):
        self.stop_cover_audio_or_video()
        self.stop_payload_audio_or_video()
        self.root.destroy()


if __name__ == "__main__":
    SteganographyApp()
