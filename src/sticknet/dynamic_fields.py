from rest_framework import serializers

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DynamicFieldsViewMixin(object):

 def get_serializer(self, *args, **kwargs):

    serializer_class = self.get_serializer_class()

    fields = None
    if self.request.method == 'GET':
        query_fields = self.request.query_params.get("fields", None)

        if query_fields:
            fields = tuple(query_fields.split(','))


    kwargs['context'] = self.get_serializer_context()
    kwargs['fields'] = fields

    return serializer_class(*args, **kwargs)


def get_serializer_context(self):
    """
    Extra context provided to the serializer class.
    """
    return {
        'request': self.request,
        'format': self.format_kwarg,
        'view': self
    }

