import django_tables2 as tables


class CollectionTable(tables.Table):
    plant_id = tables.Column(verbose_name='Plant ID', linkify=('plants:collection-detail', [tables.A('pk')]))
    species = tables.Column(accessor='species.full_name', linkify=('plants:species-detail', [tables.A('species.pk')]))
    garden_name = tables.Column(verbose_name='Garden Name', accessor='garden.name')
    garden_area = tables.Column(verbose_name='Garden Area', accessor='garden.area')
    garden_code = tables.Column(verbose_name='Garden Code', accessor='garden.code')

    class Meta:
        attrs = {"id": "collection-list-table", "class": "table"}
