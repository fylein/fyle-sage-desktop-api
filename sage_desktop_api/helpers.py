from django.db import models

class StringNotNullField(models.CharField):
    description = "Custom String with Not Null "

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 255)  # Set a default max_length
        kwargs['null'] = False  # Ensure the field is not nullable
        kwargs['help_text'] = kwargs.get('help_text', 'string field with null false')
        super(StringNotNullField, self).__init__(*args, **kwargs)

class StringNullField(models.CharField):
    description = "Custom String with Null"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 255)  # Set a default max_length
        kwargs['null'] = True  # Ensure the field is nullable
        kwargs['help_text'] = kwargs.get('help_text', 'string field with null True')
        super(StringNullField, self).__init__(*args, **kwargs)

class CustomDateTimeField(models.DateTimeField):
    description = "Custom DateTime Field with Auto-Add Now"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = True
        super(CustomDateTimeField, self).__init__(*args, **kwargs)

class TextNotNullField(models.TextField):
    description = "Custom Text Field with Not Null"

    def __init__(self, *args, **kwargs):
        kwargs['null'] = False  # Ensure the field is not nullable
        kwargs['help_text'] = kwargs.get('help_text', 'text field with null false')
        super(TextNotNullField, self).__init__(*args, **kwargs)

class StringOptionsField(models.CharField):
    description = "Custom String Field with Options"

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', [])  # Retrieve choices from kwargs
        max_length = kwargs.pop('max_length', 255)  # Retrieve max_length from kwarg
        default = kwargs.pop('default', '')
        kwargs['help_text'] = kwargs.get('help_text', 'string field with options')
        kwargs['null'] = True
        super(StringOptionsField, self).__init__(
            max_length=max_length,
            choices=choices,
            default=default,
            **kwargs
        )


class BooleanFalseField(models.BooleanField):
    description = "Custom Boolean Field with Default True"

    def __init__(self, *args, **kwargs):
        kwargs['default'] = True  # Set the default value to True
        super(BooleanFalseField, self).__init__(*args, **kwargs)

    def toggle(self, instance):
        """
        Toggle the value of the boolean field for the given instance.
        """
        value = getattr(instance, self.attname)
        setattr(instance, self.attname, not value)
        instance.save()


class BooleanTrueField(models.BooleanField):
    description = "Custom Boolean Field with Default True"

    def __init__(self, *args, **kwargs):
        kwargs['default'] = True  # Set the default value to True
        super(BooleanTrueField, self).__init__(*args, **kwargs)

    def toggle(self, instance):
        """
        Toggle the value of the boolean field for the given instance.
        """
        value = getattr(instance, self.attname)
        setattr(instance, self.attname, not value)
        instance.save()
