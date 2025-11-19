import django_tables2 as tables


class CollectionTable(tables.Table):
    plant_id = tables.Column(verbose_name='Plant ID', linkify=('plants:collection-detail', [tables.A('pk')]))
    species = tables.Column(verbose_name='Full Name', accessor='species__full_name', linkify=('plants:species-detail', [tables.A('species__pk')]))
    garden_name = tables.Column(verbose_name='Garden Name', accessor='garden__name')
    garden_area = tables.Column(verbose_name='Garden Area', accessor='garden__area')
    garden_code = tables.Column(verbose_name='Garden Code', accessor='garden__code')

    class Meta:
        attrs = {"id": "collection-list-table", "class": "table"}


class TopTreesSpeciesTable(tables.Table):
    species = tables.Column(verbose_name='Full Name', accessor='full_name', linkify=('plants:species-detail', [tables.A('pk')]))
    common_name = tables.Column(verbose_name='Common Name', accessor='vernacular_name')
    habit = tables.Column(accessor='habit')

    class Meta:
        attrs = {"id": "collection-list-table", "class": "table"}
