<?php

declare(strict_types=1);

namespace App\Helpers;

use App\Models\ApiModelAssets;
use App\Models\ApiModelInventoryRecords;
use App\Models\ApiModelLocations;
use App\Models\ApiModelPersonnel;
use App\Models\ApiModelSurplus;
use App\Models\ApiModelUsers;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Validator;
use Illuminate\Validation\Rule;
use Illuminate\Validation\ValidationException;
use Throwable;

class ApiManagerAcontarSac
{
    private const MAX_RESULTS_LIMIT = 10;
    public function __construct() {}

    public function ping(): JsonResponse
    {
        return $this->success([
            'server_time' => now()->format('Y-m-d H:i:s'),
            'timezone' => config('app.timezone'),
        ], 'Servidor disponible.');
    }

    private function resolveResultsLimit(array $data): int
    {
        $validator = Validator::make(
            $data,
            [
                'limit' => [
                    'sometimes',
                    'integer',
                    'min:1',
                    'max:' . self::MAX_RESULTS_LIMIT,
                ],
            ],
            [
                'limit.integer' => 'El parámetro limit debe ser un número entero.',
                'limit.min' => 'El parámetro limit debe ser mayor que cero.',
                'limit.max' => sprintf(
                    'El parámetro limit no puede ser mayor que %d.',
                    self::MAX_RESULTS_LIMIT
                ),
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        return (int) ($validator->validated()['limit'] ?? self::MAX_RESULTS_LIMIT);
    }

    public function initialSync(
        mixed $pdo = null,
        array $data = []
    ): JsonResponse {
        try {
            $limit = $this->resolveResultsLimit($data);

            return $this->success([
                'assets' => ApiModelAssets::query()
                    ->orderBy('id')
                    ->limit($limit)
                    ->get(),
                'locations' => ApiModelLocations::query()
                    ->orderBy('id')
                    ->limit($limit)
                    ->get(),
                'personnel' => ApiModelPersonnel::query()
                    ->orderBy('id')
                    ->limit($limit)
                    ->get(),
                'surplus' => ApiModelSurplus::query()
                    ->orderBy('id')
                    ->limit($limit)
                    ->get(),
                'inventory_records' => ApiModelInventoryRecords::query()
                    ->orderBy('id')
                    ->limit($limit)
                    ->get(),
                'limit' => $limit,
                'server_time' => now()->format('Y-m-d H:i:s'),
            ], 'Sincronización inicial obtenida correctamente.');
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible obtener la sincronización inicial.',
                $data
            );
        }
    }

    public function getRecordsByOffice(
        mixed $pdo,
        array $data
    ): JsonResponse {
        $validator = Validator::make(
            $data,
            [
                'office_id' => [
                    'required',
                    'string',
                    'max:65535',
                ],
                'limit' => [
                    'sometimes',
                    'integer',
                    'min:1',
                    'max:' . self::MAX_RESULTS_LIMIT,
                ],
            ],
            [
                'office_id.required' => 'El parámetro office_id es obligatorio.',
                'office_id.string' => 'El parámetro office_id debe ser una cadena de texto.',
                'limit.integer' => 'El parámetro limit debe ser un número entero.',
                'limit.min' => 'El parámetro limit debe ser mayor que cero.',
                'limit.max' => sprintf(
                    'El parámetro limit no puede ser mayor que %d.',
                    self::MAX_RESULTS_LIMIT
                ),
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();

            $officeId = trim((string) $validated['office_id']);
            $limit = (int) (
                $validated['limit']
                ?? self::MAX_RESULTS_LIMIT
            );

            $firstLocationRecords = ApiModelInventoryRecords::query()
                ->where('codigo_ubicacion_inicial', $officeId)
                ->orderBy('id')
                ->limit($limit)
                ->get();

            $lastLocationRecords = ApiModelInventoryRecords::query()
                ->where('codigo_ubicacion_final', $officeId)
                ->where('inventariado', true)
                ->orderBy('id')
                ->limit($limit)
                ->get();

            $missingRecords = ApiModelInventoryRecords::query()
                ->where('codigo_ubicacion_inicial', $officeId)
                ->where('inventariado', false)
                ->orderBy('id')
                ->limit($limit)
                ->get();

            $surplusRecords = ApiModelSurplus::query()
                ->where('codigo_ubicacion', $officeId)
                ->orderBy('id')
                ->limit($limit)
                ->get();

            return $this->success([
                'office_id' => $officeId,
                'limit' => $limit,
                'total_primera_ubicacion' => $firstLocationRecords->count(),
                'total_ultima_ubicacion' => $lastLocationRecords->count(),
                'total_faltantes' => $missingRecords->count(),
                'total_sobrantes' => $surplusRecords->count(),
                'primera_ubicacion' => $firstLocationRecords,
                'ultima_ubicacion' => $lastLocationRecords,
                'faltantes' => $missingRecords,
                'sobrantes' => $surplusRecords,
            ], 'Registros de la oficina obtenidos correctamente.');
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible obtener los registros de la oficina.',
                $data
            );
        }
    }
    public function dashboard(mixed $pdo = null): JsonResponse
    {
        try {
            $statistics = ApiModelInventoryRecords::query()
                ->selectRaw('COUNT(*) AS total_bienes')
                ->selectRaw(
                    'SUM(CASE WHEN inventariado = 1 THEN 1 ELSE 0 END) AS inventariados'
                )
                ->selectRaw(
                    'SUM(CASE WHEN inventariado = 0 THEN 1 ELSE 0 END) AS faltantes'
                )
                ->first();

            $total = (int) ($statistics?->total_bienes ?? 0);
            $inventoried = (int) ($statistics?->inventariados ?? 0);
            $missing = (int) ($statistics?->faltantes ?? 0);
            $surplus = ApiModelSurplus::query()->count();

            $progress = $total > 0
                ? round(($inventoried / $total) * 100, 2)
                : 0.0;

            return $this->success([
                'total_bienes' => $total,
                'inventariados' => $inventoried,
                'faltantes' => $missing,
                'sobrantes' => $surplus,
                'avance_porcentaje' => $progress,
            ], 'Datos del dashboard obtenidos correctamente.');
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible obtener los datos del dashboard.'
            );
        }
    }

    public function syncRecords(mixed $pdo, array $data): JsonResponse
    {
        $validator = Validator::make(
            $data,
            [
                'records' => ['required', 'array', 'min:1'],
                'records.*.asset_id' => [
                    'required',
                    'integer',
                    'exists:inventory_records,asset_id',
                ],
                'records.*.inventariado' => ['required', 'boolean'],
                'records.*.codigo_ubicacion_inicial' => [
                    'sometimes',
                    'nullable',
                    'string',
                    'max:65535',
                ],
                'records.*.codigo_ubicacion_final' => [
                    'sometimes',
                    'nullable',
                    'string',
                    'max:65535',
                ],
                'records.*.observacion' => [
                    'sometimes',
                    'nullable',
                    'string',
                    'max:65535',
                ],
                'records.*.fecha_inventariado' => [
                    'sometimes',
                    'nullable',
                    'date',
                ],
                'records.*.user_id' => [
                    'sometimes',
                    'integer',
                    'min:0',
                ],
            ],
            [
                'records.required' => 'No hay registros para sincronizar.',
                'records.array' => 'Los registros deben enviarse como un arreglo.',
                'records.min' => 'Debe enviar al menos un registro.',
                'records.*.asset_id.required' => 'El asset_id es obligatorio.',
                'records.*.asset_id.exists' => 'Uno de los bienes enviados no existe.',
                'records.*.inventariado.required' => 'El estado de inventariado es obligatorio.',
                'records.*.inventariado.boolean' => 'El estado de inventariado no es válido.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $records = $validator->validated()['records'];

            $result = DB::transaction(function () use ($records): array {
                $updated = 0;
                $notFound = [];

                foreach ($records as $recordData) {
                    $record = ApiModelInventoryRecords::query()
                        ->where('asset_id', $recordData['asset_id'])
                        ->lockForUpdate()
                        ->first();

                    if ($record === null) {
                        $notFound[] = $recordData['asset_id'];

                        continue;
                    }

                    $record->fill([
                        'inventariado' => (bool) $recordData['inventariado'],
                        'codigo_ubicacion_inicial' => $recordData['codigo_ubicacion_inicial'] ?? $record->codigo_ubicacion_inicial,
                        'codigo_ubicacion_final' => $recordData['codigo_ubicacion_final'] ?? $record->codigo_ubicacion_final,
                        'observacion' => $recordData['observacion']
                            ?? $record->observacion,
                        'fecha_inventariado' => $recordData['fecha_inventariado']
                            ?? $record->fecha_inventariado,
                        'user_id' => $recordData['user_id']
                            ?? $record->user_id,
                        'fecha_servidor' => now(),
                    ]);

                    if ($record->isDirty()) {
                        $record->save();
                        $updated++;
                    }
                }

                return [
                    'registros_recibidos' => count($records),
                    'registros_actualizados' => $updated,
                    'asset_ids_no_encontrados' => $notFound,
                ];
            });

            return $this->success([
                ...$result,
                'server_time' => now()->format('Y-m-d H:i:s'),
            ], 'Sincronización completada correctamente.');
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible sincronizar los registros.',
                $data
            );
        }
    }

    public function syncChanges(
        mixed $pdo,
        array $data
    ): JsonResponse {
        $validator = Validator::make(
            $data,
            [
                'last_sync' => [
                    'required',
                    'date',
                ],
                'limit' => [
                    'sometimes',
                    'integer',
                    'min:1',
                    'max:' . self::MAX_RESULTS_LIMIT,
                ],
            ],
            [
                'last_sync.required' => 'El parámetro last_sync es obligatorio.',
                'last_sync.date' => 'El parámetro last_sync no contiene una fecha válida.',
                'limit.integer' => 'El parámetro limit debe ser un número entero.',
                'limit.min' => 'El parámetro limit debe ser mayor que cero.',
                'limit.max' => sprintf(
                    'El parámetro limit no puede ser mayor que %d.',
                    self::MAX_RESULTS_LIMIT
                ),
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();

            $lastSync = (string) $validated['last_sync'];
            $limit = (int) (
                $validated['limit']
                ?? self::MAX_RESULTS_LIMIT
            );

            return $this->success([
                'server_time' => now()->format('Y-m-d H:i:s'),
                'limit' => $limit,
                'changes' => [
                    'inventory_records' => ApiModelInventoryRecords::query()
                        ->where('updated_at', '>', $lastSync)
                        ->orderBy('updated_at')
                        ->orderBy('id')
                        ->limit($limit)
                        ->get(),
                    'surplus' => ApiModelSurplus::query()
                        ->where('updated_at', '>', $lastSync)
                        ->orderBy('updated_at')
                        ->orderBy('id')
                        ->limit($limit)
                        ->get(),
                    'personnel' => ApiModelPersonnel::query()
                        ->where('updated_at', '>', $lastSync)
                        ->orderBy('updated_at')
                        ->orderBy('id')
                        ->limit($limit)
                        ->get(),
                    'locations' => ApiModelLocations::query()
                        ->where('updated_at', '>', $lastSync)
                        ->orderBy('updated_at')
                        ->orderBy('id')
                        ->limit($limit)
                        ->get(),
                    'assets' => ApiModelAssets::query()
                        ->where('updated_at', '>', $lastSync)
                        ->orderBy('updated_at')
                        ->orderBy('id')
                        ->limit($limit)
                        ->get(),
                ],
            ], 'Cambios obtenidos correctamente.');
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible obtener los cambios.',
                $data
            );
        }
    }

    public function updateUbicacionFinal(mixed $pdo, array $data): JsonResponse
    {
        $validator = Validator::make(
            $data,
            [
                'id' => ['required', 'integer', 'exists:inventory_records,id'],
                'codigo_ubicacion_final' => [
                    'required',
                    'string',
                    'min:1',
                    'not_regex:/^\\s*$/',
                    'max:65535',
                    'exists:locations,codigo_ubicacion',
                ],
                'user_id' => ['required', 'integer', 'exists:users,id'],
            ],
            [
                'id.required' => 'El ID del registro es obligatorio.',
                'id.exists' => 'No se encontró el bien.',
                'codigo_ubicacion_final.required' => 'La ubicación final es obligatoria.',
                'user_id.required' => 'El usuario es obligatorio.',
                'user_id.exists' => 'El usuario indicado no existe.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();
            $validated['codigo_ubicacion_final'] = trim(
                $validated['codigo_ubicacion_final']
            );

            $result = DB::transaction(function () use ($validated): array {
                $record = ApiModelInventoryRecords::query()
                    ->lockForUpdate()
                    ->findOrFail($validated['id']);

                if ($record->inventariado) {
                    return [
                        'already_inventoried' => true,
                        'record' => $record,
                    ];
                }

                $record->forceFill([
                    'codigo_ubicacion_final' => $validated['codigo_ubicacion_final'],
                    'inventariado' => true,
                    'user_id' => $validated['user_id'],
                    'fecha_inventariado' => now(),
                    'fecha_servidor' => now(),
                ])->save();

                return [
                    'already_inventoried' => false,
                    'record' => $record->fresh(['asset', 'user']),
                ];
            });

            if ($result['already_inventoried']) {
                $record = $result['record'];

                return $this->error(
                    'El bien ya fue inventariado por otro usuario.',
                    409,
                    [
                        'id' => $record->id,
                        'codigo_interno' => $record->codigo_interno,
                        'codigo_patrimonial' => $record->codigo_patrimonial,
                        'codigo_ubicacion_final' => $record->codigo_ubicacion_final,
                        'user_id' => $record->user_id,
                        'fecha_inventariado' => $record->fecha_inventariado,
                    ]
                );
            }

            return $this->success(
                $result['record'],
                'Bien inventariado correctamente.'
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible inventariar el bien.',
                $data
            );
        }
    }

    public function uninventoryRecord(mixed $pdo, array $data): JsonResponse
    {
        $validator = Validator::make(
            $data,
            [
                'id' => ['required', 'integer', 'exists:inventory_records,id'],
            ],
            [
                'id.required' => 'El ID del registro es obligatorio.',
                'id.exists' => 'No se encontró el registro de inventario.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $record = DB::transaction(function () use ($validator): ApiModelInventoryRecords {
                $record = ApiModelInventoryRecords::query()
                    ->lockForUpdate()
                    ->findOrFail($validator->validated()['id']);

                $record->forceFill([
                    'inventariado' => false,
                    'codigo_ubicacion_final' => '',
                    'user_id' => 0,
                    'fecha_servidor' => now(),
                ])->save();

                return $record->fresh();
            });

            return $this->success(
                $record,
                'Bien desinventariado correctamente.'
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible desinventariar el bien.',
                $data
            );
        }
    }

    public function uploadPhoto(mixed $pdo = null): JsonResponse
    {
        $validator = Validator::make(
            [
                ...request()->except('photo'),
                'photo' => request()->file('photo'),
            ],
            [
                'id' => ['required', 'integer', 'exists:inventory_records,id'],
                'user_id' => ['required', 'integer', 'exists:users,id'],
                'photo' => [
                    'required',
                    'file',
                    'image',
                    'mimes:jpg,jpeg,png',
                    'max:10240',
                ],
            ],
            [
                'id.required' => 'El ID del registro es obligatorio.',
                'id.exists' => 'No se encontró el registro de inventario.',
                'user_id.required' => 'El usuario es obligatorio.',
                'user_id.exists' => 'El usuario indicado no existe.',
                'photo.required' => 'No se recibió ninguna fotografía.',
                'photo.image' => 'El archivo enviado no es una imagen válida.',
                'photo.mimes' => 'Solo se permiten fotografías JPG, JPEG o PNG.',
                'photo.max' => 'La fotografía no puede superar los 10 MB.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        $validated = $validator->validated();

        try {
            $photo = $validated['photo'];

            if (!$photo instanceof UploadedFile) {
                return $this->error('La fotografía enviada no es válida.', 422);
            }

            $storedPath = null;

            $record = DB::transaction(function () use (
                $validated,
                $photo,
                &$storedPath
            ): ApiModelInventoryRecords {
                $record = ApiModelInventoryRecords::query()
                    ->lockForUpdate()
                    ->findOrFail($validated['id']);

                $extension = strtolower(
                    $photo->getClientOriginalExtension() ?: $photo->extension()
                );

                $fileName = sprintf(
                    '%d_%s_%s.%s',
                    $record->id,
                    now()->format('Ymd_His'),
                    bin2hex(random_bytes(4)),
                    $extension
                );

                $storedPath = $photo->storeAs(
                    'uploads/photos',
                    $fileName,
                    'public'
                );

                $previousPhoto = $record->foto_url;

                $record->forceFill([
                    'foto_url' => $storedPath,
                    'user_id' => $validated['user_id'],
                    'fecha_servidor' => now(),
                ])->save();

                if (
                    is_string($previousPhoto)
                    && $previousPhoto !== ''
                    && $previousPhoto !== $storedPath
                ) {
                    Storage::disk('public')->delete($previousPhoto);
                }

                return $record->fresh();
            });

            return $this->success([
                'record' => $record,
                'foto_url' => Storage::url((string) $storedPath),
                'foto_path' => $storedPath,
            ], 'Fotografía subida correctamente.');
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            if (isset($storedPath) && is_string($storedPath)) {
                Storage::disk('public')->delete($storedPath);
            }

            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible guardar la fotografía.',
                request()->except('photo')
            );
        }
    }

    public function updateTechnicalDetails(mixed $pdo, array $data): JsonResponse
    {
        $validator = Validator::make(
            $data,
            [
                'id' => ['required', 'integer', 'exists:inventory_records,id'],
                'user_id' => ['required', 'integer', 'exists:users,id'],
                'marca' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'modelo' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'tipo' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'color' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'serie' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'dimension' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'otros' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'situacion' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'estado_conservacion' => [
                    'sometimes',
                    'nullable',
                    'string',
                    'max:65535',
                ],
                'observacion' => ['sometimes', 'nullable', 'string', 'max:65535'],
            ],
            [
                'id.required' => 'El ID del registro es obligatorio.',
                'id.exists' => 'No se encontró el registro de inventario.',
                'user_id.required' => 'El usuario es obligatorio.',
                'user_id.exists' => 'El usuario indicado no existe.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();
            $id = $validated['id'];

            unset($validated['id']);

            $record = DB::transaction(function () use (
                $id,
                $validated
            ): ApiModelInventoryRecords {
                $record = ApiModelInventoryRecords::query()
                    ->lockForUpdate()
                    ->findOrFail($id);

                foreach (
                    [
                        'marca',
                        'modelo',
                        'tipo',
                        'color',
                        'serie',
                        'dimension',
                        'otros',
                        'situacion',
                        'estado_conservacion',
                        'observacion',
                    ] as $field
                ) {
                    if (array_key_exists($field, $validated)) {
                        $validated[$field] ??= '';
                    }
                }

                $record->forceFill([
                    ...$validated,
                    'fecha_servidor' => now(),
                ])->save();

                return $record->fresh();
            });

            return $this->success(
                $record,
                'Datos técnicos actualizados correctamente.'
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible actualizar los datos técnicos.',
                $data
            );
        }
    }

    public function createUser(mixed $pdo, array $data): JsonResponse
    {
        $validator = Validator::make(
            $data,
            [
                'nombres' => ['required', 'string', 'max:255'],
                'apellidos' => ['required', 'string', 'max:255'],
                'correo' => [
                    'nullable',
                    'email:rfc',
                    'max:255',
                    Rule::unique('users', 'correo'),
                ],
                'usuario' => [
                    'required',
                    'string',
                    'max:255',
                    Rule::unique('users', 'usuario'),
                ],
                'password' => ['required', 'string', 'min:8', 'max:255'],
                'rol' => ['sometimes', 'string', 'max:50'],
                'estado' => ['sometimes', 'boolean'],
            ],
            [
                'nombres.required' => 'Los nombres son obligatorios.',
                'apellidos.required' => 'Los apellidos son obligatorios.',
                'correo.email' => 'El correo electrónico no es válido.',
                'correo.unique' => 'El correo electrónico ya está registrado.',
                'usuario.required' => 'El nombre de usuario es obligatorio.',
                'usuario.unique' => 'El nombre de usuario ya existe.',
                'password.required' => 'La contraseña es obligatoria.',
                'password.min' => 'La contraseña debe tener al menos 8 caracteres.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();

            $user = DB::transaction(function () use ($validated): ApiModelUsers {
                return ApiModelUsers::query()->create([
                    'nombres' => trim($validated['nombres']),
                    'apellidos' => trim($validated['apellidos']),
                    'correo' => isset($validated['correo'])
                        ? trim((string) $validated['correo'])
                        : null,
                    'usuario' => trim($validated['usuario']),
                    'password_hash' => Hash::make($validated['password']),
                    'rol' => $validated['rol'] ?? 'inventariador',
                    'estado' => $validated['estado'] ?? true,
                    'token' => null,
                ]);
            });

            return $this->success(
                $user,
                'Usuario creado correctamente.',
                201
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible crear el usuario.',
                $this->removeSensitiveData($data)
            );
        }
    }

    public function createOrUpdateLocation(
        mixed $pdo,
        array $data
    ): JsonResponse {
        $id = isset($data['id']) ? (int) $data['id'] : null;

        $validator = Validator::make(
            $data,
            [
                'id' => ['sometimes', 'integer', 'exists:locations,id'],
                'codigo_ubicacion' => [
                    'required',
                    'string',
                    'max:65535',
                    Rule::unique('locations', 'codigo_ubicacion')->ignore($id),
                ],
                'local' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'area' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'oficina' => ['required', 'string', 'max:65535'],
                'piso' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'direccion' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'codigo_personal' => [
                    'sometimes',
                    'nullable',
                    'string',
                    'max:65535',
                ],
            ],
            [
                'id.exists' => 'La ubicación indicada no existe.',
                'codigo_ubicacion.required' => 'El código de ubicación es obligatorio.',
                'codigo_ubicacion.unique' => 'El código de ubicación ya existe.',
                'oficina.required' => 'La oficina es obligatoria.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();
            $locationId = $validated['id'] ?? null;

            unset($validated['id']);

            $payload = [
                'codigo_ubicacion' => trim($validated['codigo_ubicacion']),
                'local' => trim((string) ($validated['local'] ?? '')),
                'area' => trim((string) ($validated['area'] ?? '')),
                'oficina' => trim($validated['oficina']),
                'piso' => trim((string) ($validated['piso'] ?? '')),
                'direccion' => trim((string) ($validated['direccion'] ?? '')),
                'codigo_personal' => trim(
                    (string) ($validated['codigo_personal'] ?? '')
                ),
            ];

            $result = DB::transaction(function () use (
                $locationId,
                $payload
            ): array {
                if ($locationId !== null) {
                    $location = ApiModelLocations::withTrashed()
                        ->lockForUpdate()
                        ->findOrFail($locationId);

                    $location->restore();
                    $location->fill($payload);
                    $location->save();

                    return [
                        'action' => 'updated',
                        'location' => $location->fresh(),
                    ];
                }

                $location = ApiModelLocations::query()->create($payload);

                return [
                    'action' => 'created',
                    'location' => $location,
                ];
            });

            return $this->success(
                $result,
                $result['action'] === 'created'
                    ? 'Ubicación creada correctamente.'
                    : 'Ubicación actualizada correctamente.',
                $result['action'] === 'created' ? 201 : 200
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible guardar la ubicación.',
                $data
            );
        }
    }

    public function createOrUpdatePersonnel(
        mixed $pdo,
        array $data
    ): JsonResponse {
        $personnel = isset($data['codigo_personal'])
            ? ApiModelPersonnel::withTrashed()
            ->where('codigo_personal', trim((string) $data['codigo_personal']))
            ->first()
            : null;

        $validator = Validator::make(
            $data,
            [
                'codigo_personal' => [
                    'required',
                    'string',
                    'max:100',
                    Rule::unique('personnel', 'codigo_personal')
                        ->ignore($personnel?->id),
                ],
                'nombres' => ['required', 'string', 'max:100'],
                'apellidos' => ['required', 'string', 'max:100'],
                'cargo' => ['sometimes', 'nullable', 'string', 'max:100'],
                'oficina' => ['sometimes', 'nullable', 'string', 'max:65535'],
                'telefono' => ['sometimes', 'nullable', 'string', 'max:30'],
                'email' => ['sometimes', 'nullable', 'email:rfc', 'max:150'],
                'estado' => ['sometimes', 'boolean'],
            ],
            [
                'codigo_personal.required' => 'El código personal es obligatorio.',
                'codigo_personal.unique' => 'El código personal ya está registrado.',
                'nombres.required' => 'Los nombres son obligatorios.',
                'apellidos.required' => 'Los apellidos son obligatorios.',
                'email.email' => 'El correo electrónico no es válido.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();
            $code = trim($validated['codigo_personal']);

            $result = DB::transaction(function () use (
                $code,
                $validated
            ): array {
                $personnel = ApiModelPersonnel::withTrashed()
                    ->where('codigo_personal', $code)
                    ->lockForUpdate()
                    ->first();

                $payload = [
                    'codigo_personal' => $code,
                    'nombres' => trim($validated['nombres']),
                    'apellidos' => trim($validated['apellidos']),
                    'cargo' => trim((string) ($validated['cargo'] ?? '')),
                    'oficina' => trim((string) ($validated['oficina'] ?? '')),
                    'telefono' => trim((string) ($validated['telefono'] ?? '')),
                    'email' => isset($validated['email'])
                        ? trim((string) $validated['email'])
                        : null,
                    'estado' => $validated['estado'] ?? true,
                ];

                if ($personnel !== null) {
                    $personnel->restore();
                    $personnel->fill($payload);
                    $personnel->save();

                    return [
                        'action' => 'updated',
                        'personnel' => $personnel->fresh(),
                    ];
                }

                $personnel = ApiModelPersonnel::query()->create($payload);

                return [
                    'action' => 'created',
                    'personnel' => $personnel,
                ];
            });

            return $this->success(
                $result,
                $result['action'] === 'created'
                    ? 'Personal registrado correctamente.'
                    : 'Personal actualizado correctamente.',
                $result['action'] === 'created' ? 201 : 200
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible guardar los datos del personal.',
                $data
            );
        }
    }

    public function createOrUpdateSurplus(
        mixed $pdo,
        array $data
    ): JsonResponse {
        $validator = Validator::make(
            $data,
            [
                'id' => ['sometimes', 'integer', 'exists:surplus,id'],
                'codigo_ubicacion' => ['required', 'integer', 'min:0'],
                'codigo_personal' => ['required', 'integer', 'min:0'],
                'denominacion' => ['required', 'string', 'max:65535'],
                'marca' => ['required', 'string', 'max:65535'],
                'modelo' => ['required', 'string', 'max:65535'],
                'tipo' => ['required', 'string', 'max:65535'],
                'color' => ['required', 'string', 'max:65535'],
                'serie' => ['required', 'string', 'max:65535'],
                'dimension' => ['required', 'string', 'max:65535'],
                'otros' => ['required', 'string', 'max:65535'],
                'situacion' => ['required', 'string', 'max:65535'],
                'estado_conservacion' => [
                    'required',
                    'string',
                    'max:65535',
                ],
                'observacion' => ['required', 'string', 'max:65535'],
            ],
            [
                'id.exists' => 'El sobrante indicado no existe.',
                'codigo_ubicacion.required' => 'El código de ubicación es obligatorio.',
                'codigo_personal.required' => 'El código personal es obligatorio.',
                'denominacion.required' => 'La denominación es obligatoria.',
                'marca.required' => 'La marca es obligatoria.',
                'modelo.required' => 'El modelo es obligatorio.',
                'tipo.required' => 'El tipo es obligatorio.',
                'color.required' => 'El color es obligatorio.',
                'serie.required' => 'La serie es obligatoria.',
                'dimension.required' => 'La dimensión es obligatoria.',
                'otros.required' => 'El campo otros es obligatorio.',
                'situacion.required' => 'La situación es obligatoria.',
                'estado_conservacion.required' => 'El estado de conservación es obligatorio.',
                'observacion.required' => 'La observación es obligatoria.',
            ]
        );

        if ($validator->fails()) {
            throw new ValidationException($validator);
        }

        try {
            $validated = $validator->validated();
            $surplusId = $validated['id'] ?? null;

            unset($validated['id']);

            $result = DB::transaction(function () use (
                $surplusId,
                $validated
            ): array {
                if ($surplusId !== null) {
                    $surplus = ApiModelSurplus::withTrashed()
                        ->lockForUpdate()
                        ->findOrFail($surplusId);

                    $surplus->restore();
                    $surplus->fill($validated);
                    $surplus->save();

                    return [
                        'action' => 'updated',
                        'surplus' => $surplus->fresh(),
                    ];
                }

                $surplus = ApiModelSurplus::query()->create($validated);

                return [
                    'action' => 'created',
                    'surplus' => $surplus,
                ];
            });

            return $this->success(
                $result,
                $result['action'] === 'created'
                    ? 'Sobrante registrado correctamente.'
                    : 'Sobrante actualizado correctamente.',
                $result['action'] === 'created' ? 201 : 200
            );
        } catch (ValidationException $exception) {
            throw $exception;
        } catch (Throwable $exception) {
            return $this->serverError(
                $exception,
                __METHOD__,
                'No fue posible guardar el sobrante.',
                $data
            );
        }
    }

    private function success(
        mixed $data = null,
        string $message = '',
        int $status = 200
    ): JsonResponse {
        return response()->json([
            'success' => true,
            'message' => $message,
            'data' => $data,
        ], $status);
    }

    private function error(
        string $message,
        int $status = 400,
        mixed $data = null
    ): JsonResponse {
        return response()->json([
            'success' => false,
            'message' => $message,
            'data' => $data,
        ], $status);
    }

    private function serverError(
        Throwable $exception,
        string $method,
        string $message,
        array $context = []
    ): JsonResponse {
        Log::error($message, [
            'class' => self::class,
            'method' => $method,
            'context' => $this->removeSensitiveData($context),
            'exception' => $exception::class,
            'error' => $exception->getMessage(),
            'trace' => $exception->getTraceAsString(),
        ]);

        return $this->error(
            $message,
            500,
            app()->hasDebugModeEnabled()
                ? ['error' => $exception->getMessage()]
                : null
        );
    }

    private function removeSensitiveData(array $data): array
    {
        foreach (
            [
                'password',
                'password_confirmation',
                'password_hash',
                'token',
                'authorization',
            ] as $field
        ) {
            if (array_key_exists($field, $data)) {
                $data[$field] = '[REDACTED]';
            }
        }

        return $data;
    }
}
