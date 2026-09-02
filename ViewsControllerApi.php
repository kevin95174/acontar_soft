<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Helpers\ApiManagerAcontarSac;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ViewsControllerApi extends Controller
{
    /**
     * Inicializa el controlador e inyecta el gestor principal de la API.
     *
     * @param ApiManagerAcontarSac $apiManager Gestor encargado de ejecutar
     *                                                las operaciones de la API.
     */
    public function __construct(
        private readonly ApiManagerAcontarSac $apiManager
    ) {}

    /**
     * Responde con un error 404 para rutas no reconocidas por la API.
     *
     * @param string|null $any Segmento opcional capturado desde la ruta.
     *
     * @return never
     */
    public function index(?string $any = null): never
    {
        abort(404, 'Página no encontrada');
    }

    /**
     * Verifica que el servidor y la API se encuentren disponibles.
     *
     * No requiere datos de entrada.
     *
     * @param Request $request Solicitud HTTP recibida.
     *
     * @return JsonResponse Respuesta con el estado del servidor,
     *                      la fecha y la zona horaria configurada.
     */
    public function ping(Request $request): JsonResponse
    {
        return $this->apiManager->ping();
    }

    /**
     * Obtiene la información inicial necesaria para sincronizar un cliente.
     *
     * Devuelve bienes, ubicaciones, personal, sobrantes y registros
     * de inventario disponibles en el servidor.
     *
     * No requiere datos de entrada.
     *
     * @param Request $request Solicitud HTTP recibida.
     *
     * @return JsonResponse Respuesta con los datos de sincronización inicial.
     */
    public function initial_sync(Request $request): JsonResponse
    {
        return $this->apiManager->initialSync();
    }

    /**
     * Obtiene los registros de inventario asociados a una oficina.
     *
     * Datos de entrada esperados:
     * - office_id: Código de la oficina o ubicación que se desea consultar.
     *
     * @param Request $request Solicitud HTTP con el código de la oficina.
     *
     * @return JsonResponse Respuesta con registros iniciales, finales,
     *                      faltantes, sobrantes y totales de la oficina.
     */
    public function get_records_by_office(Request $request): JsonResponse
    {
        return $this->apiManager->getRecordsByOffice(
            null,
            $request->all()
        );
    }

    /**
     * Obtiene los indicadores generales del inventario.
     *
     * No requiere datos de entrada.
     *
     * @param Request $request Solicitud HTTP recibida.
     *
     * @return JsonResponse Respuesta con el total de bienes, inventariados,
     *                      faltantes, sobrantes y porcentaje de avance.
     */
    public function dashboard(Request $request): JsonResponse
    {
        return $this->apiManager->dashboard();
    }

    /**
     * Sincroniza múltiples registros de inventario enviados por un cliente.
     *
     * Datos de entrada esperados:
     * - records: Arreglo de registros que se desean sincronizar.
     * - records.*.asset_id: Identificador del bien.
     * - records.*.inventariado: Estado de inventariado.
     * - records.*.codigo_ubicacion_inicial: Ubicación inicial opcional.
     * - records.*.codigo_ubicacion_final: Ubicación final opcional.
     * - records.*.observacion: Observación opcional.
     * - records.*.fecha_inventariado: Fecha de inventariado opcional.
     * - records.*.user_id: Identificador del usuario opcional.
     *
     * @param Request $request Solicitud HTTP con los registros a sincronizar.
     *
     * @return JsonResponse Respuesta con la cantidad de registros recibidos,
     *                      actualizados y no encontrados.
     */
    public function sync_records(Request $request): JsonResponse
    {
        return $this->apiManager->syncRecords(
            null,
            $request->all()
        );
    }

    /**
     * Obtiene los registros modificados desde la última sincronización.
     *
     * Datos de entrada esperados:
     * - last_sync: Fecha y hora de la última sincronización del cliente.
     *
     * @param Request $request Solicitud HTTP con la fecha de última sincronización.
     *
     * @return JsonResponse Respuesta con los cambios de bienes, ubicaciones,
     *                      personal, sobrantes y registros de inventario.
     */
    public function sync_changes(Request $request): JsonResponse
    {
        return $this->apiManager->syncChanges(
            null,
            $request->all()
        );
    }

    /**
     * Registra la ubicación final de un bien y lo marca como inventariado.
     *
     * Datos de entrada esperados:
     * - id: Identificador del registro de inventario.
     * - codigo_ubicacion_final: Código de la ubicación final.
     * - user_id: Identificador del usuario que realiza la operación.
     *
     * @param Request $request Solicitud HTTP con la ubicación final del bien.
     *
     * @return JsonResponse Respuesta con el registro actualizado o un conflicto
     *                      cuando el bien ya fue inventariado.
     */
    public function update_ubicacion_final(Request $request): JsonResponse
    {
        return $this->apiManager->updateUbicacionFinal(
            null,
            $request->all()
        );
    }

    /**
     * Revierte el estado de inventariado de un registro.
     *
     * Datos de entrada esperados:
     * - id: Identificador del registro de inventario.
     *
     * La operación elimina la ubicación final y marca el registro
     * como no inventariado.
     *
     * @param Request $request Solicitud HTTP con el identificador del registro.
     *
     * @return JsonResponse Respuesta con el registro desinventariado.
     */
    public function uninventory_record(Request $request): JsonResponse
    {
        return $this->apiManager->uninventoryRecord(
            null,
            $request->all()
        );
    }

    /**
     * Sube y relaciona una fotografía con un registro de inventario.
     *
     * La solicitud debe utilizar multipart/form-data.
     *
     * Datos de entrada esperados:
     * - id: Identificador del registro de inventario.
     * - user_id: Identificador del usuario que carga la fotografía.
     * - photo: Archivo de imagen JPG, JPEG o PNG.
     *
     * @param Request $request Solicitud HTTP con el archivo de fotografía.
     *
     * @return JsonResponse Respuesta con el registro actualizado,
     *                      la URL pública y la ruta de la fotografía.
     */
    public function upload_photo(Request $request): JsonResponse
    {
        return $this->apiManager->uploadPhoto();
    }

    /**
     * Actualiza los datos técnicos de un bien inventariado.
     *
     * Datos de entrada esperados:
     * - id: Identificador del registro de inventario.
     * - user_id: Identificador del usuario que realiza la actualización.
     * - marca: Marca del bien, opcional.
     * - modelo: Modelo del bien, opcional.
     * - tipo: Tipo del bien, opcional.
     * - color: Color del bien, opcional.
     * - serie: Número de serie, opcional.
     * - dimension: Dimensiones del bien, opcional.
     * - otros: Información técnica adicional, opcional.
     * - situacion: Situación actual del bien, opcional.
     * - estado_conservacion: Estado de conservación, opcional.
     * - observacion: Observaciones adicionales, opcional.
     *
     * @param Request $request Solicitud HTTP con los datos técnicos.
     *
     * @return JsonResponse Respuesta con el registro actualizado.
     */
    public function update_technical_details(Request $request): JsonResponse
    {
        return $this->apiManager->updateTechnicalDetails(
            null,
            $request->all()
        );
    }

    /**
     * Crea un nuevo usuario para el sistema.
     *
     * Datos de entrada esperados:
     * - nombres: Nombres del usuario.
     * - apellidos: Apellidos del usuario.
     * - correo: Correo electrónico opcional.
     * - usuario: Nombre de usuario único.
     * - password: Contraseña sin cifrar.
     * - rol: Rol del usuario, opcional.
     * - estado: Estado activo o inactivo, opcional.
     *
     * La contraseña será cifrada antes de almacenarse.
     *
     * @param Request $request Solicitud HTTP con los datos del nuevo usuario.
     *
     * @return JsonResponse Respuesta con el usuario creado.
     */
    public function create_user(Request $request): JsonResponse
    {
        return $this->apiManager->createUser(
            null,
            $request->all()
        );
    }

    /**
     * Crea una ubicación o actualiza una ubicación existente.
     *
     * Datos de entrada esperados:
     * - id: Identificador de la ubicación, opcional para actualización.
     * - codigo_ubicacion: Código único de la ubicación.
     * - local: Nombre del local, opcional.
     * - area: Área de la ubicación, opcional.
     * - oficina: Nombre de la oficina.
     * - piso: Piso de la ubicación, opcional.
     * - direccion: Dirección física, opcional.
     * - codigo_personal: Código del responsable, opcional.
     *
     * Cuando se envía el campo id, se actualiza la ubicación correspondiente.
     * Cuando no se envía, se crea una nueva ubicación.
     *
     * @param Request $request Solicitud HTTP con los datos de la ubicación.
     *
     * @return JsonResponse Respuesta con la ubicación creada o actualizada.
     */
    public function create_or_update_location(Request $request): JsonResponse
    {
        return $this->apiManager->createOrUpdateLocation(
            null,
            $request->all()
        );
    }

    /**
     * Crea o actualiza un registro de personal.
     *
     * Datos de entrada esperados:
     * - codigo_personal: Código único del personal.
     * - nombres: Nombres del personal.
     * - apellidos: Apellidos del personal.
     * - cargo: Cargo desempeñado, opcional.
     * - oficina: Oficina asignada, opcional.
     * - telefono: Número telefónico, opcional.
     * - email: Correo electrónico, opcional.
     * - estado: Estado activo o inactivo, opcional.
     *
     * Si el código personal ya existe, el registro será actualizado.
     * En caso contrario, se creará un nuevo registro.
     *
     * @param Request $request Solicitud HTTP con los datos del personal.
     *
     * @return JsonResponse Respuesta con el personal creado o actualizado.
     */
    public function create_or_update_personnel(Request $request): JsonResponse
    {
        return $this->apiManager->createOrUpdatePersonnel(
            null,
            $request->all()
        );
    }

    /**
     * Crea o actualiza un bien sobrante detectado durante el inventario.
     *
     * Datos de entrada esperados:
     * - id: Identificador del sobrante, opcional para actualización.
     * - codigo_ubicacion: Código de la ubicación.
     * - codigo_personal: Código del personal responsable.
     * - denominacion: Denominación del bien.
     * - marca: Marca del bien.
     * - modelo: Modelo del bien.
     * - tipo: Tipo del bien.
     * - color: Color del bien.
     * - serie: Número de serie.
     * - dimension: Dimensión del bien.
     * - otros: Información adicional.
     * - situacion: Situación actual del bien.
     * - estado_conservacion: Estado de conservación.
     * - observacion: Observaciones adicionales.
     *
     * Cuando se envía el campo id, se actualiza el sobrante correspondiente.
     * Cuando no se envía, se crea un nuevo registro.
     *
     * @param Request $request Solicitud HTTP con los datos del bien sobrante.
     *
     * @return JsonResponse Respuesta con el sobrante creado o actualizado.
     */
    public function create_or_update_surplus(Request $request): JsonResponse
    {
        return $this->apiManager->createOrUpdateSurplus(
            null,
            $request->all()
        );
    }
}
