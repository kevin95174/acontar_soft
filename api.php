<?php

Route::post('/query/response/initial_sync', [ViewsControllerApi::class, 'initial_sync'])
    ->name('api.query.initial-sync');
Route::post('/query/response/get_records_by_office', [ViewsControllerApi::class, 'get_records_by_office'])
    ->name('api.query.records-by-office');
Route::post('/query/response/dashboard', [ViewsControllerApi::class, 'dashboard'])
    ->name('api.query.dashboard');
Route::post('/query/response/sync_records', [ViewsControllerApi::class, 'sync_records'])
    ->name('api.query.sync-records');
Route::post('/query/response/sync_changes', [ViewsControllerApi::class, 'sync_changes'])
    ->name('api.query.sync-changes');
Route::post('/query/response/update_ubicacion_final', [ViewsControllerApi::class, 'update_ubicacion_final'])
    ->name('api.query.update-final-location');
Route::post('/query/response/uninventory_record', [ViewsControllerApi::class, 'uninventory_record'])
    ->name('api.query.uninventory-record');
Route::post('/query/response/upload_photo', [ViewsControllerApi::class, 'upload_photo'])
    ->name('api.query.upload-photo');
Route::post('/query/response/update_technical_details', [ViewsControllerApi::class, 'update_technical_details'])
    ->name('api.query.update-technical-details');
Route::post('/query/response/create_user', [ViewsControllerApi::class, 'create_user'])
    ->name('api.query.create-user');
Route::post('/query/response/create_or_update_location', [ViewsControllerApi::class, 'create_or_update_location'])
    ->name('api.query.create-or-update-location');
Route::post('/query/response/create_or_update_personnel', [ViewsControllerApi::class, 'create_or_update_personnel'])
    ->name('api.query.create-or-update-personnel');
Route::post('/query/response/create_or_update_surplus', [ViewsControllerApi::class, 'create_or_update_surplus'])
    ->name('api.query.create-or-update-surplus');
