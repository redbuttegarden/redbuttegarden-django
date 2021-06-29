from rest_framework.fields import ListField

class StringArrayField(ListField):
    """
    String representation of an array field.
    """
    def to_representation(self, obj):
        obj = super().to_representation(obj)
        # convert list to string
        return ",".join([str(element) for element in obj])

    def to_internal_value(self, data):
        data = data.split(",")  # convert string to list
        return super().to_internal_value(data)
