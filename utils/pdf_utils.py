import os
from PIL import Image
from reportlab.lib.utils import ImageReader
from utils.config_utils import ConfigUtils
from datetime import date
from reportlab.pdfgen import canvas

class PageNumCanvas(canvas.Canvas):

    def __init__(self, *args, fecha=None, orientacion=0, logo_path=None, mostrar_logo=True, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        self.fecha = fecha
        self.orientacion = orientacion
        self.logo_path = logo_path
        self.mostrar_logo = mostrar_logo

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)
        
    def draw_page_number(self, page_count):
        # Determinar ruta del logo (prioridad: parámetro personalizado, luego config.ini)
        image_path = self.logo_path
        if not image_path:
            config_instance = ConfigUtils()
            direccion = config_instance.load_config()
            image_path = direccion[1] if (direccion and len(direccion) > 1) else None

        page = "Página %s de %s" % (self._pageNumber, page_count)        
        if self.fecha:
            today = "Fecha: " + self.fecha    
        else:
            today = date.today()
            today = "Fecha: " + today.strftime("%d/%m/%Y")

        self.setFont("Helvetica", 9)

        # Carga segura del logo (si mostrar_logo es True y el archivo existe)
        imagen = None
        new_width = 0
        new_height_pdf = 50
        if self.mostrar_logo and image_path and os.path.exists(image_path):
            try:
                image = Image.open(image_path)
                aspect_ratio = image.width / image.height
                new_width = new_height_pdf * aspect_ratio
                imagen = ImageReader(image_path)
            except Exception:
                imagen = None

        if self.orientacion == 1:
            self.drawRightString(530, 20, page)
            self.drawRightString(120, 20, str(today))
            if imagen:
                self.drawImage(imagen, 60, 780, width=new_width, height=new_height_pdf)
        else:    
            self.drawRightString(800, 20, page)
            self.drawRightString(120, 20, str(today))
            if imagen:
                self.drawImage(imagen, 40, 535, width=new_width, height=new_height_pdf)
