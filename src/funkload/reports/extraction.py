from docutils.core import publish_doctree

def extract_table(table):
    column_names = [elem for elem in table.traverse() if elem.tagname == 'thead'][0][0]
    # Extract all rows from the table except the header row
    rows = [elem for elem in table.traverse() if elem.tagname == 'row'][1:]

    columns = {}
    for idx, column in enumerate(column_names):
        columns[column.astext()] = [row[idx].astext() for row in rows]

    return columns


def extract_report_data(report_path):
    with open(report_path) as report:
        doc = publish_doctree(''.join(report.readlines()))

    # All stats tables are marked with a comment before-hand with the table
    # title in it
    stats_table_tag = 'stats_table '
    stats_table_markers = [elem for elem in doc.traverse()
        if (elem.tagname == 'comment' and
            elem[0].astext().startswith(stats_table_tag))]

    stats_tables = [extract_table(m.next_node(siblings=True, descend=False))
        for m in stats_table_markers]

    return dict(zip(
        (e[0].astext()[len(stats_table_tag):] for e in stats_table_markers),
        stats_tables
    ))


