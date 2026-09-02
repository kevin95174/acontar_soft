def sort_by(tree, column, descending):
    """Ordenar los datos por la columna especificada en el widget treeview."""
    try:
        data = [(tree.set(child, column), child) for child in tree.get_children('')]
        data.sort(key=lambda x: float(x[0]), reverse=descending)
        for index, (_, child) in enumerate(data):
            tree.move(child, '', index)
    except:
        data = [(tree.set(child, column), child) for child in tree.get_children('')]
        data.sort(reverse=descending)
        for index, (_, child) in enumerate(data):
            tree.move(child, '', index)

    total_item = None
    for item in tree.get_children(''):
        values = tree.item(item, 'values')
        if values and values[0] == 'TOTALES':
            total_item = item
            break
    if total_item:
        tree.move(total_item, '', 'end')