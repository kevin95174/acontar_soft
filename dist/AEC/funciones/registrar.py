import tkinter as tk
from tkinter import ttk

class test_nv(tk.Toplevel):
    def __init__(self, frame_app,root=None):
        super().__init__(root)
        self.root = root
        self.frame_app = frame_app
        self.title("Test")


        btn = ttk.Button(self, text="Boton", command=lambda:self.test())
        btn.grid(column=0, row=0)

    def test(self):
        if self.frame_app:
            self.frame_app.registrar(101,str(213))
