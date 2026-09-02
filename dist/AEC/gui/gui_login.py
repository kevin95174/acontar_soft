import tkinter as tk
from tkinter import Toplevel, ttk
from PIL import ImageTk, Image
from tkinter import messagebox as mb
from db.query import login, login_register, login_user
from gui.gui_app import Frame

class Frame_login(ttk.Frame):

	def __init__(self, root=None):
		super().__init__(root)
		self.root = root
		self.pack(fill='both')

		self.FrameU = tk.Frame(self, bg="#585858")
		self.FrameU.pack(fill='both')
		self.FrameU.config(width=800, height=500)
		self.FrameU.rowconfigure(0, weight=1)
		self.FrameU.columnconfigure(0, weight=1)

		self.Frame1 = tk.Frame(self.FrameU, bg="#585858")
		self.Frame1.pack(side="right", fill='both', padx=10, pady=1)

		self.Frame1_1 = tk.Frame(self.Frame1, bg="#585858")
		self.Frame1_1.pack(side="top", expand=True)
		self.Frame1_2 = tk.Frame(self.Frame1, bg="#585858")
		self.Frame1_2.pack(side="bottom", expand=True)
		
		self.Frame2 = tk.Frame(self.FrameU)
		self.Frame2.pack(side="left", expand=True)
		
		self.vNomb = tk.StringVar()
		self.vApat = tk.StringVar()
		self.vAmat = tk.StringVar()
		self.vNdni = tk.StringVar()
		self.vUser = tk.StringVar()
		self.vPass = tk.StringVar()
		self.vEqui = tk.StringVar()
		
		self.image = Image.open("img/user.png")
		self.resize_img = self.image.resize((170, 170))
		self.img = ImageTk.PhotoImage(self.resize_img)
		self.lblImg = tk.Label(self.Frame1_1, image=self.img, bg="#585858")
		self.lblImg.pack(fill="both", side="top", padx=5, pady=1)
		
		self.bkg = Image.open("img/login_.jpg")
		self.resize_bkg = self.bkg.resize((420, 400))
		self.img_bkg = ImageTk.PhotoImage(self.resize_bkg)
		self.lblbkg = ttk.Label(self.FrameU, image=self.img_bkg)
		self.lblbkg.pack(fill="both")

		self.user = tk.StringVar()
		self.passw = tk.StringVar()

			# Labels
		self.lblUser = tk.Label(self.Frame1_2, text="Usuario", bg="#585858", 
		fg="#ffffff", font=("Helvetica-Bold", 12)).grid(column=0, row=0, padx=5, pady=10, sticky="w")
		self.lblPass = tk.Label(self.Frame1_2, text="Contraseña", bg="#585858", 
		fg="#ffffff", font=("Helvetica-Bold", 12)).grid(column=0, row=1, padx=5, pady=1, sticky="w")

			# Entrys
		self.etrUser = ttk.Entry(self.Frame1_2, textvariable= self.user)
		self.etrUser.grid(column=1, row=0, padx=5, pady=1, sticky="ew")
		self.etrPass = ttk.Entry(self.Frame1_2, textvariable= self.passw, show="*").grid(column=1, row=1,padx=5, pady=1, sticky="ew")

			# Buttons
		self.btnEtr = tk.Button(self.Frame1_2, text="Entrar", bg="#e30613", 
		fg="#ffffff", font=("Helvetica-Bold", 10),command=lambda:login_test())
		self.btnEtr.grid(column=1, row=3, padx=5, pady=10, sticky="ew")
		
		self.btnReg = tk.Button(self.Frame1_2, text="Registrar", bg="#e30613", 
		fg="#ffffff", font=("Helvetica-Bold", 10),command=lambda:abrir_ventana()).grid(column=1, row=4, padx=5, pady=1, sticky="ew")
		self.etrUser.focus_set()

		def login_test():
			u = self.user.get()
			p = self.passw.get()
			try:
				r = login(u, p)
				if r == 1:
					j = login_user(u, p)
					name = j[0][0]
					Ndni = j[0][1]
					team = j[0][2]
					self.pack_forget()
					Frame(root, name, Ndni, team)
					# barra_menu(root)
				else:
					mb.showwarning(message="Error al ingresar", title="Atencion")
				return name
			except:
				pass

		def abrir_ventana():
			reg = Toplevel(self)
			reg.title("Acontar Especialistas Contables")
			reg.iconbitmap('img/favicon.ico')
			reg.geometry("300x400")

			lblNomb = ttk.Label(reg, text="Nombre").grid(column=0, row=0, padx=5, pady=1, sticky="ew")
			lblApat = ttk.Label(reg, text="Apellido Pat").grid(column=0, row=1, padx=5, pady=1, sticky="ew")
			lblAmat = ttk.Label(reg, text="Apellido Mat").grid(column=0, row=2, padx=5, pady=1, sticky="ew")
			lblNdni = ttk.Label(reg, text="DNI").grid(column=0, row=3, padx=5, pady=1, sticky="ew")
			lblUser = ttk.Label(reg, text="Usuario").grid(column=0, row=4, padx=5, pady=1, sticky="ew")
			lblPass = ttk.Label(reg, text="Password").grid(column=0, row=5, padx=5, pady=1, sticky="ew")
			lblEqui = ttk.Label(reg, text="Equipo").grid(column=0, row=6, padx=5, pady=1, sticky="ew")

			etrNomb = ttk.Entry(reg, textvariable = self.vNomb).grid(column=1, row=0, padx=5, pady=1, sticky="ew")
			etrApat = ttk.Entry(reg, textvariable = self.vApat).grid(column=1, row=1, padx=5, pady=1, sticky="ew")
			etrAmat = ttk.Entry(reg, textvariable = self.vAmat).grid(column=1, row=2, padx=5, pady=1, sticky="ew")
			etrNdni = ttk.Entry(reg, textvariable = self.vNdni).grid(column=1, row=3, padx=5, pady=1, sticky="ew")
			etrUser = ttk.Entry(reg, textvariable = self.vUser)
			etrUser.grid(column=1, row=4, padx=5, pady=1, sticky="ew")
			etrPass = ttk.Entry(reg, textvariable = self.vPass).grid(column=1, row=5, padx=5, pady=1, sticky="ew")
			etrEqui = ttk.Entry(reg, textvariable = self.vEqui).grid(column=1, row=6, padx=5, pady=1, sticky="ew")

			btnRegU = ttk.Button(reg, text="Registrar", command=lambda:registrar_user()).grid(column=1, row=7, padx=5, pady=1, sticky="ew")

			def registrar_user():
				try:
					u = self.vUser.get()
					login_register(u, self.vPass.get(), self.vNomb.get(), self.vApat.get(), self.vAmat.get(), self.vNdni.get(), self.vEqui.get())
					mb.showinfo(message="Registrado exitosamente", title="AEC SAC")
				except:
					mb.showerror(message="Mensaje de error", title="¡Atencion")					
