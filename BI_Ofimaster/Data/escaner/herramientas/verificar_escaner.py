"""Verifica el circuito documental con documentos/cantidades FICTICIOS aislados."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
from unittest.mock import patch

from automatizacion.piloto_local import preparar, entorno_piloto, ruta_piloto


def pdf_ficticio(etiqueta, paginas=1):
    from PIL import Image, ImageDraw
    from io import BytesIO
    imagen = Image.new('RGB', (1000, 1200), 'white')
    dibujo = ImageDraw.Draw(imagen)
    dibujo.text((40, 60), 'DOCUMENTO FICTICIO - NO OPERACIONAL\nFACTURA NRO 12345\nOC 4500999002\n' + etiqueta, fill='black')
    salida = BytesIO()
    imagen.save(salida, format='PDF', save_all=True, append_images=[imagen] * (paginas - 1))
    imagen.close()
    return salida.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nombre', required=True, help='Nombre nuevo para pruebas ficticias.')
    args = parser.parse_args()
    preparar(args.nombre, date.today())
    os.environ.update(entorno_piloto(args.nombre))
    from fastapi.testclient import TestClient
    from app.principal import app
    from app.servicios.revision_documental import RevisionDocumental
    from app.servicios.control_acceso import permits
    from app.servicios.identidad_microsoft import permite
    from app.servicios.extraccion_documental import extraer
    from app.servicios.documentos_recepcion import DocumentosRecepcion
    raiz = ruta_piloto(args.nombre)
    documentos = DocumentosRecepcion(raiz / 'documentos_recepcion')
    controles = []
    with TestClient(app) as cliente:
        pdf = pdf_ficticio('PRIMER ESCANEO')
        r = cliente.post('/api/documentos-recepcion/cargar', files={'archivo': ('../ficticio.pdf', pdf, 'application/pdf')})
        assert r.status_code == 200, r.text
        identidad = r.json()['id']
        assert r.json()['registro_operacional'] is False
        controles.append('carga_pdf_sin_ruta_suministrada_ni_recepcion')
        assert cliente.post('/api/documentos-recepcion/cargar', files={'archivo': ('malo.pdf', b'%PDF-no valido', 'application/pdf')}).status_code == 400
        assert cliente.post('/api/documentos-recepcion/cargar', files={'archivo': ('otro.pdf', b'invalido', 'application/pdf')}, headers={'origin': 'https://otro.example'}).status_code == 403
        controles.append('pdf_corrupto_y_origen_externo_rechazados')
        assert cliente.get(f'/api/documentos-recepcion/{identidad}/paginas/1').status_code == 200
        assert cliente.get(f'/api/documentos-recepcion/{identidad}/paginas/2').status_code == 404
        assert cliente.get(f'/api/documentos-recepcion/{identidad}/extraccion').json()['estado'] == 'SIN_EXTRACCION'
        # Comprobar contrato de extracción sin confundirlo con precisión del OCR real.
        class MotorFicticio:
            def leer(self, imagen):
                return [{'texto': 'FACTURA NRO 12345 OC 4500999002', 'confianza': 0.9, 'caja': None}]
        extraer(documentos, identidad, motor=MotorFicticio(), modo='ocr')
        lectura = cliente.get(f'/api/documentos-recepcion/{identidad}/extraccion').json()
        assert lectura['paginas'][0]['candidatos']['oc'] == ['4500999002']
        controles.append('visor_y_extraccion_solo_propuesta')
        lineas = cliente.get('/api/operacion/recepciones/lotes').json()['items']
        actual = next(l for l in lineas if l['oc'] == '4500999002')
        linea = {'id': actual['id'], 'version': actual['version'], 'recibidas': 6, 'aceptadas': 5, 'rechazadas': 1,
            'codigo_documento': actual['material'], 'unidad_documento': 'EA', 'unidad_registro': 'EA',
            'evidencia_unidad': 'FICTICIO: unidad declarada solo para esta prueba, no SAP.',
            'factor_numerador': 1, 'factor_denominador': 1,
            'recibidas_documento': 6, 'aceptadas_documento': 5, 'rechazadas_documento': 1}
        datos = {'version': '', 'rut_emisor': '76075072-7', 'tipo_documento': 'FACTURA', 'folio': '12345',
            'responsable': 'Usuario de prueba', 'fecha': date.today().isoformat(),
            'nota': 'RECEPCION FICTICIA - NO USAR EN OPERACION', 'oc': actual['oc'], 'lineas': [linea]}
        url = f'/api/documentos-recepcion/{identidad}'
        assert cliente.post(url + '/borrador', json={**datos, 'oc': 'OC-INEXISTENTE'}).status_code == 400
        assert cliente.post(url + '/borrador', json={**datos, 'lineas': [{**linea, 'aceptadas': 7}]}).status_code == 400
        assert cliente.post(url + '/borrador', json={**datos, 'lineas': [{**linea, 'factor_numerador': 2}]}).status_code == 400
        exceso = {**linea, 'recibidas': 1001, 'recibidas_documento': 1001}
        assert cliente.post(url + '/borrador', json={**datos, 'lineas': [exceso]}).status_code == 400
        assert cliente.post(url + '/borrador', json={**datos, 'lineas': [{**linea, 'version': 'obsoleta'}]}).status_code == 400
        controles.append('oc_cantidad_y_conversion_incoherentes_rechazadas')
        r = cliente.post(url + '/borrador', json=datos)
        assert r.status_code == 200, r.text
        borrador = r.json()
        antes = cliente.get('/api/operacion/recepciones/lotes').json()['items']
        assert next(l for l in antes if l['id'] == actual['id'])['fisicas'] == actual['fisicas']
        assert cliente.post(url + '/borrador', json=datos).status_code == 400
        assert cliente.post(url + '/confirmar', json={'version': borrador['version'], 'verificado': False}).status_code == 400
        controles.append('borrador_sin_entrega_y_version_obsoleta_rechazada')
        original = RevisionDocumental.escribir
        def fallo_despues_excel(self, ruta, estado):
            if estado['estado'] == 'REGISTRADO':
                raise OSError('Fallo simulado antes de persistir confirmación documental.')
            return original(self, ruta, estado)
        with patch.object(RevisionDocumental, 'escribir', new=fallo_despues_excel):
            r = cliente.post(url + '/confirmar', json={'version': borrador['version'], 'verificado': True})
            assert r.status_code == 409, r.text
        assert cliente.get(url + '/borrador').json()['estado'] == 'CONFIRMANDO'
        r = cliente.post(url + '/confirmar', json={'version': borrador['version'], 'verificado': True})
        assert r.status_code == 200 and r.json()['estado'] == 'REGISTRADO', r.text
        assert cliente.post(url + '/confirmar', json={'version': borrador['version'], 'verificado': True}).status_code == 200
        finales = cliente.get('/api/operacion/recepciones/lotes').json()
        final = next(l for l in finales['items'] if l['id'] == actual['id'])
        assert final['fisicas'] == actual['fisicas'] + 6 and final['aceptadas'] == 5 and final['rechazadas'] == 1
        assert len([l for l in finales['historial'] if l['Evento'] == 'DOC-' + identidad]) == 1
        controles.append('fallo_reintento_y_confirmacion_repetida_sin_doble_entrega')
        # Un nuevo escaneo tiene hash diferente pero la misma identidad comercial.
        segundo = cliente.post('/api/documentos-recepcion/cargar', files={'archivo': ('segundo.pdf', pdf_ficticio('NUEVO ESCANEO'), 'application/pdf')}).json()['id']
        nueva = {**datos, 'lineas': [{**linea, 'version': final['version']}]}
        r = cliente.post(f'/api/documentos-recepcion/{segundo}/borrador', json=nueva)
        assert r.status_code == 200, r.text
        assert cliente.post(f'/api/documentos-recepcion/{segundo}/confirmar', json={'version': r.json()['version'], 'verificado': True}).status_code == 400
        controles.append('nuevo_escaneo_factura_duplicada_bloqueado')
        repetido = cliente.post('/api/documentos-recepcion/cargar', files={'archivo': ('otra-copia.pdf', pdf, 'application/pdf')})
        assert repetido.status_code == 200 and repetido.json()['id'] == identidad
        assert cliente.get(url + '/borrador').json()['estado'] == 'REGISTRADO'
        controles.append('recarga_pdf_no_reemplaza_confirmacion')
        multiple = cliente.post('/api/documentos-recepcion/cargar', files={'archivo': ('paginas.pdf', pdf_ficticio('DOS PAGINAS FICTICIAS', 2), 'application/pdf')})
        assert multiple.status_code == 200, multiple.text
        id_multiple = multiple.json()['id']
        assert cliente.post(f'/api/documentos-recepcion/{id_multiple}/borrador', json=nueva).status_code == 400
        r = cliente.post(f'/api/documentos-recepcion/{id_multiple}/borrador', json={**nueva, 'folio': '12346', 'documento_individual_verificado': True})
        assert r.status_code == 200, r.text
        controles.append('pdf_multipagina_exige_clasificacion_humana')
        class MotorInterrumpido:
            llamadas = 0
            def leer(self, imagen):
                self.llamadas += 1
                if self.llamadas > 1:
                    raise ValueError('Fallo simulado en la segunda página.')
                return [{'texto': 'OCR FICTICIO DE LA PRIMERA PAGINA', 'confianza': 0.8, 'caja': None}]
        try:
            extraer(documentos, id_multiple, modo='ocr', motor=MotorInterrumpido())
        except ValueError:
            pass
        else:
            raise AssertionError('No se simuló la interrupción esperada.')
        parcial = documentos.extraccion(id_multiple)
        assert len(parcial['paginas']) == 1 and parcial['completa'] is False
        extraer(documentos, id_multiple, modo='ocr', motor=MotorFicticio(), reprocesar=True)
        assert documentos.extraccion(id_multiple)['completa'] is True
        controles.append('extraccion_interrumpida_conserva_paginas_y_permite_reintento')
        from app.servicios.extraccion_documental import MotorConLimite
        import subprocess
        with patch('app.servicios.extraccion_documental.subprocess.run', side_effect=subprocess.TimeoutExpired('ocr', 10)):
            try:
                MotorConLimite(10).leer(documentos.imagen(id_multiple, 1))
            except ValueError as error:
                assert '10 segundos' in str(error)
            else:
                raise AssertionError('No se aplicó el timeout OCR.')
        controles.append('tiempo_maximo_ocr_controlado')
        assert permits('recepcion', 'POST', '/api/documentos-recepcion/cargar')
        assert not permits('consulta', 'POST', '/api/documentos-recepcion/cargar')
        assert permite({'permisos': ['recepcion']}, 'POST', '/api/documentos-recepcion/cargar')
        assert not permite({'permisos': ['abastecimiento']}, 'POST', '/api/documentos-recepcion/cargar')
        controles.append('reglas_de_permiso_basic_y_microsoft')
    informe = {'ok': True, 'controles': controles, 'datos': 'FICTICIOS',
        'alcance': 'Circuito API y recuperación; no certifica precisión OCR ni identidad Microsoft en vivo.'}
    (raiz / 'reportes' / 'verificacion_escaner.json').write_text(json.dumps(informe, indent=2), encoding='utf-8')
    print(json.dumps(informe))


if __name__ == '__main__':
    main()
