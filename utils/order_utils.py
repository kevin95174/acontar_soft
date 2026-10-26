def sort_by(tree, column, descending=False):
    """Ordenar los datos por la columna especificada en el widget treeview."""
    all_children = tree.get_children('')
    total_child = None
    data = []

    for child in all_children:
        vals = tree.item(child, 'values')
        if vals and str(vals[0]).strip().upper() == 'TOTALES':
            total_child = child
            continue
        val = tree.set(child, column)
        data.append((val, child))

    def parse_val(v):
        try:
            cleaned = str(v).replace('%', '').replace(',', '').strip()
            return (0, float(cleaned))
        except (ValueError, TypeError):
            return (1, str(v).lower())

    data.sort(key=lambda x: parse_val(x[0]), reverse=descending)

    for index, (_, child) in enumerate(data):
        tree.move(child, '', index)

    if total_child:
        tree.move(total_child, '', 'end')

    # Alternar dirección para el siguiente clic
    tree.heading(column, command=lambda: sort_by(tree, column, not descending))
