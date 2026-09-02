import piexif
from db.query import datos_exif

def insertar_metadatos(barcode_info, imagen):
    metadatos = datos_exif(barcode_info)
    if metadatos:
        exif_dict = {"0th":{}, "Exif":{}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None, "thumbnail_offset": None, "thumbnail_length": None}
        xmp_str = f"""
                    <x:xmpmeta xmlns:x="adobe:ns:meta/">
                        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
                            <rdf:Description rdf:about="" xmlns:exif="http://ns.adobe.com/exif/1.0/">
                                <exif:CodInt>{metadatos["CodInt"]}</exif:CodInt>
                                <exif:ActaAnt>{metadatos["ActaAnt"]}</exif:ActaAnt>
                                <exif:Inv>{metadatos["Inv"]}</exif:Inv>
                                <exif:CodPat>{metadatos["CodPat"]}</exif:CodPat>
                                <exif:DenBien>{metadatos["DenBien"]}</exif:DenBien>
                                <exif:NroDocAdq>{metadatos["NroDocAdq"]}</exif:NroDocAdq>
                                <exif:FechAdq>{metadatos["FechAdq"]}</exif:FechAdq>
                                <exif:ValAdq>{metadatos["ValAdq"]}</exif:ValAdq>
                                <exif:DepAcum>{metadatos["DepAcum"]}</exif:DepAcum>
                                <exif:ValNeto>{metadatos["ValNeto"]}</exif:ValNeto>
                                <exif:CtaCont>{metadatos["CtaCont"]}</exif:CtaCont>
                                <exif:DenCta>{metadatos["DenCta"]}</exif:DenCta>
                                <exif:Estado>{metadatos["Estado"]}</exif:Estado>
                                <exif:Marca>{metadatos["Marca"]}</exif:Marca>
                                <exif:Modelo>{metadatos["Modelo"]}</exif:Modelo>
                                <exif:Tipo>{metadatos["Tipo"]}</exif:Tipo>
                                <exif:Color>{metadatos["Color"]}</exif:Color>
                                <exif:Serie>{metadatos["Serie"]}</exif:Serie>
                                <exif:Dimension>{metadatos["Dimension"]}</exif:Dimension>
                                <exif:Placa>{metadatos["Placa"]}</exif:Placa>
                                <exif:NroMotor>{metadatos["NroMotor"]}</exif:NroMotor>
                                <exif:NroChasis>{metadatos["NroChasis"]}</exif:NroChasis>
                                <exif:Matricula>{metadatos["Matricula"]}</exif:Matricula>
                                <exif:AñoFab>{metadatos["AñoFab"]}</exif:AñoFab>
                                <exif:Nota>{metadatos["Nota"]}</exif:Nota>
                                <exif:Obs>{metadatos["Obs"]}</exif:Obs>
                                <exif:FechInv>{metadatos["FechInv"]}</exif:FechInv>
                                <exif:Otros>{metadatos["Otros"]}</exif:Otros>
                                <exif:Situacion>{metadatos["Situacion"]}</exif:Situacion>
                                <exif:Inventariador>{metadatos["Inventariador"]}</exif:Inventariador>
                                <exif:Equipo>{metadatos["Equipo"]}</exif:Equipo>
                            </rdf:Description>
                        </rdf:RDF>
                    </x:xmpmeta>
                """
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = xmp_str.encode('utf-8')
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, imagen)