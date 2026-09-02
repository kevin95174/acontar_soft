# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
            ('data/*.*', 'data/'), 
            ('db/*.*', 'db/'), 
            ('exportar/', 'exportar/'),
            ('fichas_inventario/', 'fichas_inventario/'),
            ('funciones/*', 'funciones/'),
            ('gui/*.*','gui/'),
            ('img/*.*', 'img/'), 
            ('label/*.*', 'label/'), 
            ('labels/', 'labels/'), 
            ('photos/', 'photos/'),
            ('report_actas/', 'report_actas/'),
            ('reportes/*.*', 'reportes/'),
            ('utils/*', 'utils/'),
            ('C:\\Users\\Lenovo\\Documents\\test\\roelcode\\venv\\Lib\\site-packages\\barcode\\fonts', 'barcode/fonts'),
            ('C:\\Users\\Lenovo\\Documents\\acontar_soft\\VERSION_03\\CODIGO\\venv\\Lib\\site-packages\\pyzbar', 'pyzbar/')]

a = Analysis(
    ['root.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AEC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='img/favicon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AEC',
)
