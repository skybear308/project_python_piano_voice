from tkinter import *
import os
from tkinter import *
from tkinter import filedialog
from pygame import mixer
import tkinter.messagebox
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkFont
import sounddevice as sd
from scipy.io.wavfile import write
import subprocess
import sqlite3
from sqlite3 import Error
import hashlib, binascii, os
import time
import datetime
import wave
import pyaudio
import threading
import numpy as np

class App:

    def __init__(self, root):
        self.root = root
        self.root.geometry("300x250")
        self.root.title("Welcome")
        tk.Label(self.root, text="Welcome", bg="red", width="300", height="2", font=("Calibri", 13)).pack()
        tk.Label(text="").pack()
        tk.Button(self.root, text="Login", height="2", width="30", command=lambda: self.new_window(Login)).pack()
        tk.Label(text="").pack()
        tk.Button(self.root, text="Register", height="2", width="30", command=lambda: self.new_window(Register)).pack()

    def new_window(self, _class):
        self.new = tk.Toplevel(self.root)
        _class(self.new)

class Register:
    def __init__(self, root):
        self.root = root
        self.root.title("Register")
        self.root.geometry("300x250")

        self.username = StringVar()
        self.password = StringVar()

        tk.Label(self.root, text="Please enter details below").pack()
        tk.Label(self.root, text="").pack()
        tk.Label(self.root, text="Username * ").pack()

        self.username_entry = tk.Entry(self.root, textvariable=self.username)
        self.username_entry.pack()
        tk.Label(self.root, text="Password * ").pack()
        self.password_entry = Entry(self.root, show="*", textvariable=self.password)
        self.password_entry.pack()
        tk.Label(self.root, text="Confirm Password * ").pack()
        self.ConfirmPassword = tk.Entry(self.root, show="*", textvariable=self.password)
        self.ConfirmPassword.pack()
        tk.Label(self.root, text="").pack()
        tk.Button(self.root, text="Register", width=10, height=1, command=lambda :self.register_user()).pack()

    def register_user(self):
        print("working")

        username_info = self.username.get()
        password_info = self.password.get()

        if username_info == '' or password_info == '':
            tkinter.messagebox.showinfo("Warning", "You have to input Username and Password!")

        connection = None
        try:
            connection = sqlite3.connect("Data.db")
        except Error as e:
            print(e)
        c = connection.cursor()
        c.execute('SELECT EXISTS(SELECT username FROM User WHERE username="%s" LIMIT 1)' % username_info)
        row_exist, = c.fetchone()
        if row_exist == 1:
            tkinter.messagebox.showinfo("Warning", "User already exist!")
            return

        sql = ("INSERT INTO User(username, password) VALUES(?,?)", [username_info, self.hash_password(password_info)])

        cur = connection.cursor()
        cur.execute(*sql)
        connection.commit()

        connection.close()

        self.username_entry.delete(0, END)
        self.password_entry.delete(0, END)

        Label(self.root, text="Registration Sucess", fg="green", font=("calibri", 11)).pack()

    def hash_password(self, password):
        """Hash a password for storing."""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                      salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')


class Login:
    def __init__(self, root):
        self.root = root
        self.root.geometry("300x250")
        self.root.title("Login")
        self.root.title("Login")

        tk.Label(self.root, text="Please enter details below to login").pack()
        tk.Label(self.root, text="").pack()

        self.username_verify = StringVar()
        self.password_verify = StringVar()

        self.logged_username = ''

        tk.Label(self.root, text="Username * ").pack()
        self.username_entry1 = tk.Entry(self.root, textvariable=self.username_verify)
        self.username_entry1.pack()
        tk.Label(self.root, text="").pack()
        tk.Label(self.root, text="Password * ").pack()
        self.password_entry1 = Entry(self.root, show="*", textvariable=self.password_verify)
        self.password_entry1.pack()
        tk.Label(self.root, text="").pack()
        tk.Button(self.root, text="Login", width=10, height=1, command=lambda : self.login_verify()).pack()

        self.userNotFound = tk.Label(self.root, text="User Not Found")
        self.passwordError = tk.Label(self.root, text="Password Error")

    def login_verify(self):
        username1 = self.username_verify.get()
        password1 = self.password_verify.get()
        self.username_entry1.delete(0, END)
        self.password_entry1.delete(0, END)

        connection = None
        try:
            connection = sqlite3.connect("Data.db")
        except Error as e:
            print(e)
        c = connection.cursor()
        c.execute('SELECT password FROM User WHERE username="%s" LIMIT 1' % username1)
        row_exist = c.fetchone()
        if row_exist is None:
            self.user_not_found()
            return

        if self.verify_password(str(row_exist[0]), password1) == True:
            self.logged_username = username1
            self.new_window(Action)
        else:
            self.password_not_recognised()

    def verify_password(self, stored_password, provided_password):
        """Verify a stored password against one provided by user"""
        salt = stored_password[:64]
        stored_password = stored_password[64:]
        pwdhash = hashlib.pbkdf2_hmac('sha512',
                                      provided_password.encode('utf-8'),
                                      salt.encode('ascii'),
                                      100000)
        pwdhash = binascii.hexlify(pwdhash).decode('ascii')
        return pwdhash == stored_password

    def delete3(self):
        self.root.destroy()

    def user_not_found(self):
        self.passwordError.pack_forget()
        self.userNotFound.pack()

    def password_not_recognised(self):
        self.userNotFound.pack_forget()
        self.passwordError.pack()

    def new_window(self, _class):
        self.new = tk.Toplevel(self.root)
        _class(self.new, self.logged_username)

class Action:
    def __init__(self, root, logged_username):
        self.root = root
        self.logged_username = logged_username
        self.action_log = ''
        self.record_elapse = 0
        self.start_time = ''
        self.timestamp = ''
        self.record_duration = 0
        self.record_flag = False
        self.filename_path = ''

        self.pause = False
        self.brun = False

        self.max_volume = 40
        self.current_volume = 0

        # recorded wav file path (default:output.wav)
        self.record_path = StringVar()
        self.record_file = ""

        # Create the menubar
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # Create the submenu

        self.subMenu = tk.Menu(self.menubar, tearoff=0)
        self.subMenu1 = tk.Menu(self.menubar, tearoff=0)
        self.subMenu2 = tk.Menu(self.menubar, tearoff=0)

        self.playlist = []

        self.m_thread = threading.Thread(target=lambda :self.record_thread())

        self.menubar.add_cascade(label="File", menu=self.subMenu)
        self.subMenu.add_command(label="Open", command=lambda: self.browse_file())
        self.subMenu.add_command(label="Exit", command=lambda :self.root.destroy)
        self.subMenu.add_command(label="Save", command=lambda :self.root.destroy)

        self.menubar.add_cascade(label="Help", menu=self.subMenu1)
        self.subMenu1.add_command(label="MusicBox", command=lambda: self.about_us())
        self.subMenu1.add_command(label="About Us", command=lambda: self.about_us())

        self.menubar.add_cascade(label="Log", menu=self.subMenu2)
        self.subMenu2.add_command(label="Show Logs", command=lambda: self.new_window(ActionLog))

        self.Leftframe = tk.Frame(self.root)
        self.Leftframe.pack(side=LEFT, padx=5, pady=5)
        mixer.init()  # initialising the mixer

        self.root.title("DJ PRO ")

        self.text = tk.Label(self.root, text='Lets party')
        self.text.pack(pady=5)

        self.duration = tk.Label(self.root, text="Total length: 00:00")
        self.duration.pack()


        self.lb_playlist = tk.Label(self.Leftframe, text="Play List")
        self.lb_playlist.pack()
        self.playlistbox = tk.Listbox(self.Leftframe, height=25)
        self.playlistbox.pack()

        self.addBtn = tk.Button(self.Leftframe, text="Add +", command=lambda: self.browse_file())
        self.addBtn.pack(side=LEFT, padx=10, pady=10)

        self.delBtn = tk.Button(self.Leftframe, text="Del -", command=lambda: self.remove_file())
        self.delBtn.pack(side=LEFT, padx=10, pady=10)

        self.middleframe = tk.Frame(self.root, relief=RAISED, borderwidth=1)
        self.middleframe.pack(side=LEFT, padx=10)

        self.bottomframe = tk.Frame(self.root, borderwidth=0)
        self.bottomframe.pack(side=BOTTOM, fill=X, pady=10)

        self.playBtn = tk.Button(self.middleframe, text="Play", command=lambda: self.play_music())
        self.playBtn.pack(pady=10)

        self.stopBtn = tk.Button(self.middleframe, text="Stop", command=lambda: self.stop_music())
        self.stopBtn.pack(pady=10)

        self.RewindBtn = tk.Button(self.middleframe, text="Rewind", command=lambda: self.Rewind_music())
        self.RewindBtn.pack(pady=10)

        self.pauseBtn = tk.Button(self.middleframe, text="Pause", command=lambda: self.pause_music())
        self.pauseBtn.pack(pady=10)

        self.fadeBtn = tk.Button(self.middleframe, text="Fade", command=lambda: self.fade_music())
        self.fadeBtn.pack(pady=10)

        self.recBtn = tk.Button(self.middleframe, text="Record", command=lambda: self.record_music())
        self.recBtn.pack(pady=10)

        self.muteBtn = tk.Button(self.middleframe, text="Mute", command=lambda: self.mute_music())
        self.muteBtn.pack(pady=10)

        self.scale = Scale(self.middleframe, from_=0, to=100, resolution=4, label="", orient=HORIZONTAL,
                           command=lambda x: self.SetVolume(x))
        mixer.music.set_volume(0.2)
        self.scale.set(20)

        self.scale.pack(side=LEFT, pady=16)

        # piano
        self.ABC = tk.Frame(self.root, bg="green", bd=5, relief=RIDGE)
        self.ABC.pack(side=LEFT, padx=10, pady=10)

        self.ABC1 = tk.Frame(self.ABC, bg="white", bd=5, relief=RIDGE)
        self.ABC1.pack(padx=10, pady=10)
        self.ABC2 = tk.Frame(self.ABC, bg="red", bd=1, relief=RIDGE)
        self.ABC2.pack(padx=10, pady=10)
        self.ABC3 = tk.Frame(self.ABC, bg="white", bd=1, relief=RIDGE)
        self.ABC3.pack(padx=10, pady=10)

        self.str1 = StringVar()
        self.str1.set("Make some noise!")
        tk.Label(self.ABC1, text="Piano", font=('arial', 15, 'bold'), padx=8, pady=8, bd=4, bg="powder blue",
                 fg="black", justify=CENTER).grid(row=0, column=0, columnspan=11)
        # black keys
        self.btnCs = tk.Button(self.ABC2, height=4, width=2, text="C#", font=('arial', 10, 'bold'), fg="white", bd=4, bg="black",
                          command=lambda: self.Csharp())
        self.btnCs.grid(row=0, column=0, padx=5, pady=5)

        self.btnDs = tk.Button(self.ABC2, height=4, width=2, text="D#", font=('arial', 10, 'bold'), fg="white", bd=4, bg="black",
                          command=lambda: self.Dsharp())
        self.btnDs.grid(row=0, column=1, padx=4, pady=5)

        self.btnC1s = tk.Button(self.ABC2, height=4, width=2, text="C1#", font=('arial', 10, 'bold'), fg="white", bd=4,
                           bg="black",
                           command=lambda: self.Cs1())
        self.btnC1s.grid(row=0, column=8, padx=4, pady=5)

        self.btnFs = tk.Button(self.ABC2, height=4, width=2, text="F#", font=('arial', 10, 'bold'), fg="white", bd=4, bg="black",
                          command=lambda: self.Fsharp())
        self.btnFs.grid(row=0, column=2, padx=4, pady=5)

        self.btnGs = tk.Button(self.ABC2, height=4, width=2, text="G#", font=('arial', 10, 'bold'), fg="white", bd=4, bg="black",
                          command=lambda: self.Gsharp())
        self.btnGs.grid(row=0, column=4, padx=4, pady=5)

        self.btnBb = tk.Button(self.ABC2, height=4, width=2, text="Bb", font=('arial', 10, 'bold'), fg="white", bd=4, bg="black",
                          command=lambda: self.Bb())
        self.btnBb.grid(row=0, column=5, padx=4, pady=5)
        # space between keys
        self.space1 = tk.Button(self.ABC2, state=DISABLED, width=1, height=6, bg="red", relief=FLAT)
        self.space1.grid(row=0, column=3, padx=0, pady=0)
        self.space5 = tk.Button(self.ABC2, state=DISABLED, width=1, height=6, bg="red", relief=FLAT)
        self.space5.grid(row=0, column=9, padx=0, pady=0)
        # white keys

        self.buttonC = tk.Button(self.ABC3, bd=4, width=3, height=4, text="C", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.C())
        self.buttonC.grid(row=0, column=0, padx=5, pady=5)
        self.buttonD = tk.Button(self.ABC3, bd=4, width=3, height=4, text="D", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.D())
        self.buttonD.grid(row=0, column=1, padx=5, pady=5)
        self.buttonE = tk.Button(self.ABC3, bd=4, width=3, height=4, text="E", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.E())
        self.buttonE.grid(row=0, column=2, padx=5, pady=5)
        self.buttonF = tk.Button(self.ABC3, bd=4, width=3, height=4, text="F", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.F())
        self.buttonF.grid(row=0, column=3, padx=5, pady=5)
        self.buttonG = tk.Button(self.ABC3, bd=4, width=3, height=4, text="G", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.G())
        self.buttonG.grid(row=0, column=4, padx=5, pady=5)
        self.buttonA = tk.Button(self.ABC3, bd=4, width=3, height=4, text="A", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.A())
        self.buttonA.grid(row=0, column=5, padx=5, pady=5)
        self.buttonB = tk.Button(self.ABC3, bd=4, width=3, height=4, text="B", bg="white", fg="black",
                            font=("Verdana", 10, "bold"),
                            command=lambda: self.B())
        self.buttonB.grid(row=0, column=6, padx=5, pady=5)

        self.buttonC1 = tk.Button(self.ABC3, bd=4, width=3, height=4, text="C1", bg="white", fg="black",
                             font=("Verdana", 10, "bold"), command=lambda: self.c1())
        self.buttonC1.grid(row=0, column=7, padx=5, pady=5)
        self.buttonD1 = tk.Button(self.ABC3, bd=4, width=3, height=4, text="D1", bg="white", fg="black",
                             font=("Verdana", 10, "bold"), command=lambda: self.d1())
        self.buttonD1.grid(row=0, column=8, padx=5, pady=5)
        self.buttonE1 = tk.Button(self.ABC3, bd=4, width=3, height=4, text="E1", bg="white", fg="black",
                             font=("Verdana", 10, "bold"), command=lambda: self.e1())
        self.buttonE1.grid(row=0, column=9, padx=5, pady=5)
        self.buttonF1 = tk.Button(self.ABC3, bd=4, width=3, height=4, text="F1", bg="white", fg="black",
                             font=("Verdana", 10, "bold"), command=lambda: self.f1())
        self.buttonF1.grid(row=0, column=10, padx=5, pady=5)


        self.statubar = tk.Label(self.bottomframe, text="DJ pro", relief=SUNKEN, anchor=W)
        self.statubar.pack(side=BOTTOM, pady=5, fill=X)

        self.recordPathLabel = tk.Label(self.bottomframe, text="Recorded file name (output.wav) : ")
        self.recordPathLabel.pack(side=LEFT, pady=5)

        self.record_path = tk.Entry(self.bottomframe, textvariable=self.record_path)
        self.record_path.pack(side=LEFT)
        self.record_path.insert(0, "output.wav")
        # self.recordFileNameLabel = tk.Label(self.bottomframe, text="Recorded file name : ", anchor=W)
        # self.recordFileNameLabel.pack(side=LEFT, padx=10)

        self.root.mainloop()

    def remove_file(self):
        selected_song = self.playlistbox.curselection()
        selected_song_index = int(selected_song[0])
        self.playlistbox.delete(selected_song_index)

    def new_window(self, _class):
        self.new = tk.Toplevel(self.root)
        _class(self.new, self.logged_username)

    def browse_file(self):
        self.filename_path = filedialog.askopenfilename()
        self.Add_To_Playlist(self.filename_path)

        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Browse File" + '(' + self.action_time + ') >> '

    def Add_To_Playlist(self, filename):
        filename = os.path.basename(filename)
        index = 0
        self.playlistbox.insert(index, filename)
        self.playlist.insert(index, self.filename_path)
        self.playlistbox.pack()
        index += 1

        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Add File To List" + "(" + filename + ")" + '(' + self.action_time + ') >> '

    def about_us(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "About Us" + '(' + self.action_time + ') >> '
        tkinter.messagebox.showinfo('About us', 'Dj pro is small program written in python using tkinter')

    def showLength(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Show Length" + '(' + self.action_time + ') >> '
        s = mixer.sound("happy.mp3")
        total_length = s.get  # + length()
        print(total_length)

        mins, secs = divmod(total_length, 60)

    def record_thread(self):
        self.brun = True
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = 2
        fs = 44100  # Record at 44100 samples per second
        seconds = 100

        p = pyaudio.PyAudio()  # Create an interface to PortAudio

        print('Recording')

        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)

        frames = []  # Initialize array to store frames

        # Store data in chunks for 3 seconds
        for i in range(0, int(fs / chunk * seconds)):
            data = stream.read(chunk)
            frames.append(data)
            if self.brun == False:
                # Stop and close the stream
                stream.stop_stream()
                stream.close()
                # Terminate the PortAudio interface
                p.terminate()

                print('Finished recording')

                # Save the recorded data as a WAV file
                wf = wave.open(self.record_file, 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(sample_format))
                wf.setframerate(fs)
                wf.writeframes(b''.join(frames))
                wf.close()
                return

    def record_music(self):
        self.record_flag = not self.record_flag

        if self.record_flag == True:
            self.record_elapse = 0
            now = datetime.datetime.now()
            self.timestamp = now.strftime("%Y-%m-%d-%H:%M:%S")
            self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")
            self.action_log = "Start Record" + '(' + self.action_time + ') >> '

            self.start_time = time.time()

            # create wav file
            self.record_file = self.record_path.get()
            data = np.random.uniform(-1, 1, 44100)  # 44100 random samples between -1 and 1
            scaled = np.int16(data / np.max(np.abs(data)) * 32767)
            write(self.record_file, 44100, scaled)
            self.m_thread.start()

        else:
            connection = None
            try:
                connection = sqlite3.connect("Data.db")
            except Error as e:
                print(e)
            record_duration = time.time() - self.start_time

            now = datetime.datetime.now()
            self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")
            self.action_log += "Stop Record" + '(' + self.action_time + ')'

            sql = ("INSERT INTO ActionLog(username, actionlog, time_stamp, duration) VALUES(?,?,?,?)",
                   [self.logged_username, self.action_log, self.timestamp, record_duration])

            cur = connection.cursor()
            cur.execute(*sql)
            connection.commit()

            connection.close()
            self.brun = False
            self.m_thread.join()

    def play_music(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Play Music" + '(' + self.action_time + ') >> '

        # self.pause = False
        if self.pause:

            mixer.music.unpause()
            self.statubar['text'] = "Music Resumed"
            self.pause = False
        else:
            try:

                selected_song = self.playlistbox.curselection()
                selected_song = int(selected_song[0])
                play_it = self.playlist[selected_song]

                mixer.music.load(play_it)
                mixer.music.play()

                self.statubar['text'] = "Playing music" + ' - ' + os.path.basename(play_it)

            except Exception as e:
                print(e)
                tkinter.messagebox.showerror('File not found',
                                             'Music player could not find the file please check again')

    def stop_music(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Stop Music" + '(' + self.action_time + ') >> '
        mixer.music.stop()
        self.statubar['text'] = "Music stopped"

    def SetVolume(self, val):
        Volume = int(val) / 100
        mixer.music.set_volume(Volume)
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        if self.record_flag == True:
            self.action_log += "Set Volumn to " + str(Volume) + '(' + self.action_time + ') >> '

    def Rewind_music(self):
        self.play_music()
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")
        self.action_log += "Rewind Music" + '(' + self.action_time + ') >> '

    def pause_music(self):
        self.pause = TRUE
        mixer.music.pause()
        self.statubar['text'] = "Music Paused"
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Pause Music" + '(' + self.action_time + ') >> '

    def unPause_music(self):
        mixer.music.unpause()
        self.statubar['text'] = "Playing music" + ' ' + os.path.basename("happy.mp3")
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Unpause Music" + '(' + self.action_time + ') >> '

    def fade_music(self):
        mixer.music.fadeout(3000)
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Fade Music" + '(' + self.action_time + ') >> '

    def mute_music(self):
        mixer.music.unpause()
        self.statubar['text'] = "Music muted" + ' ' + os.path.basename("happy.mp3")
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Mute Music" + '(' + self.action_time + ') >> '

    # set the volume to the given percent using amixer
    def set_volume_to(self, percent):
        subprocess.call(["amixer", "-D", "pulse", "sset", "Master",
                         str(percent) + "%", "stdout=devnull"])
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Set Volume to" + str(percent) + '(' + self.action_time + ') >> '

    # play the song and fade in the song to the max_volume
    def play_song(self, song_file):

        print("Song starting: " + song_file)
        mixer.music.load(song_file)
        mixer.music.play()

        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Play Song" + '(' + self.action_time + ') >> '

    # giving piano buttons sounds
    def Csharp(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "C#" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\C_s.wav")
        sound.play()

    def Fsharp(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "F#" + '(' + self.action_time + ') >> '
        self.str1.set("F#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\F_s.wav")
        sound.play()

    def Gsharp(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "G#" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\G_s.wav")
        sound.play()

    def Dsharp(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "D#" + '(' + self.action_time + ') >> '
        self.str1.set("D#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\D_s.wav")
        sound.play()

    def Cs1(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Cs1" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\C_s1.wav")
        sound.play()

    def Bb(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "Bb" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\Bb.wav")
        sound.play()

    def C(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "C" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\C.wav")
        sound.play()

    def D(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "D" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\D.wav")
        sound.play()

    def E(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "E" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\E.wav")
        sound.play()

    def F(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "F" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\F.wav")
        sound.play()

    def G(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "G" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\G.wav")
        sound.play()

    def A(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "A" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\A.wav")
        sound.play()

    def B(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "B" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\B.wav")
        sound.play()

    def c1(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "c1" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\C1.wav")
        sound.play()

    def d1(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "d1" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\D1.wav")
        sound.play()

    def e1(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "e1" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\E1.wav")
        sound.play()

    def f1(self):
        now = datetime.datetime.now()
        self.action_time = now.strftime("%Y-%m-%d-%H:%M:%S")

        self.action_log += "f1" + '(' + self.action_time + ') >> '
        self.str1.set("C#")
        sound = mixer.Sound("C:\\Users\\Administrator\\OneDrive\\Documents\\python\\course work\\F1.wav")
        sound.play()

class ActionLog():

    def __init__(self, root, logged_username):
        self.root = root
        self.root.geometry("800x350")
        self.root.title("Action Logs")
        self.logged_username = logged_username
        self.CreateUI()
        self.LoadTable()

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def CreateUI(self):
        tv = ttk.Treeview(self.root)
        tv['columns'] = ('username', 'actionlog', 'time_stamp', 'duration')
        tv.heading("#0", text='No', anchor='w')
        tv.column("#0", anchor="w", width=20)
        tv.heading('username', text='UserName')
        tv.column('username', anchor='center', width=100)
        tv.heading('actionlog', text='Action Logs')
        tv.column('actionlog', anchor='center', width=400)
        tv.heading('time_stamp', text='Time Stamp')
        tv.column('time_stamp', anchor='center', width=100)
        tv.heading('duration', text='Duration')
        tv.column('duration', anchor='center', width=100)
        tv.grid(sticky=(N, S, W, E))
        self.treeview = tv
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def LoadTable(self):
        connection = None
        try:
            connection = sqlite3.connect("Data.db")
        except Error as e:
            print(e)
        c = connection.cursor()
        c.execute('SELECT * FROM ActionLog WHERE username="%s" ' % self.logged_username)

        result = c.fetchall()
        i = 1
        for x in result:
            self.treeview.insert('', 'end', text=i, values=(x[1], x[2], x[3], x[4]))
            i = i + 1
        connection.close()

root = tk.Tk()
app = App(root)
root.mainloop()
