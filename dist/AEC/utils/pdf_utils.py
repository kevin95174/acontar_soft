from PIL import Image
from reportlab.lib.utils import ImageReader
from utils.config_utils import ConfigUtils
from datetime import date
from reportlab.pdfgen import canvas

class PageNumCanvas(canvas.Canvas):

    def __init__(self, *args, fecha=None, orientacion=0,**kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []
        self.fecha = fecha
        self.orientacion = orientacion

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
        config_instance = ConfigUtils()
        direccion = config_instance.load_config()
        image_path = direccion[1]
        image = Image.open(image_path)
        # Calcular la relación de aspecto de la imagen
        aspect_ratio = image.width / image.height
        # Definir el alto fijo deseado en el PDF
        new_height_pdf = 50  # Altura fija deseada en unidades
        # Calcular el nuevo ancho en función del aspecto original y el alto fijo
        new_width = new_height_pdf * aspect_ratio
        imagen = ImageReader(image_path)
        page = "Página %s de %s" % (self._pageNumber, page_count)        
        if self.fecha:
            today = "Fecha: "+ self.fecha    
        else:
            today = date.today()
            today = "Fecha: "+today.strftime("%d/%m/%Y")

        self.setFont("Helvetica", 9)

        if self.orientacion == 1:
            self.drawRightString(530, 20, page)
            self.drawRightString(120, 20, str(today))
            self.drawImage(imagen, 60, 780, width=new_width, height=new_height_pdf)
        else:    
            self.drawRightString(800, 20, page)
            self.drawRightString(120, 20, str(today))
            self.drawImage(imagen, 40, 535, width=new_width, height=new_height_pdf)
        
        # self.drawRightString(530 if self.orientacion == 1 else 800, 20, page)
        # self.drawRightString(120, 20, str(today))
        # self.drawImage(imagen, 60 if self.orientacion == 1 else 10, 780 if self.orientacion == 1 else 535, width=new_width, height=new_height_pdf)
