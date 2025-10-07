from django import forms
from .models import Task, TaskOutputField, TaskOutput

class DynamicTaskCompletionForm(forms.Form):
    """
    Dynamically generates form fields based on TaskOutputField definitions
    """
    def __init__(self, task, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task = task
        self.user = user
        
        # Get all output fields for this task
        output_fields = task.output_fields.all()
        
        for field in output_fields:
            field_name = f'field_{field.id}'
            
            if field.field_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=field.name,
                    required=field.required,
                    widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
                )
            
            elif field.field_type == 'radio':
                if field.options:
                    choices = [(opt.strip(), opt.strip()) for opt in field.options.split(',')]
                    self.fields[field_name] = forms.ChoiceField(
                        label=field.name,
                        choices=choices,
                        widget=forms.RadioSelect(),  # REMOVED attrs={'class': 'form-check-input'}
                        required=field.required
                    )
            
            elif field.field_type == 'checkbox':
                if field.options:
                    choices = [(opt.strip(), opt.strip()) for opt in field.options.split(',')]
                    self.fields[field_name] = forms.MultipleChoiceField(
                        label=field.name,
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple(),  # REMOVED attrs={'class': 'form-check-input'}
                        required=field.required
                    )
            
            elif field.field_type == 'yesno':
                self.fields[field_name] = forms.ChoiceField(
                    label=field.name,
                    choices=[('yes', 'Yes'), ('no', 'No')],
                    widget=forms.RadioSelect(),  # REMOVED attrs={'class': 'form-check-input'}
                    required=field.required
                )
            
            elif field.field_type == 'number':
                self.fields[field_name] = forms.FloatField(
                    label=field.name,
                    required=field.required,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': 'any'
                    })
                )
                # Add help text for min/max
                if field.min_value or field.max_value:
                    help_parts = []
                    if field.min_value is not None:
                        help_parts.append(f"Min: {field.min_value}")
                    if field.max_value is not None:
                        help_parts.append(f"Max: {field.max_value}")
                    self.fields[field_name].help_text = " | ".join(help_parts)
            
            elif field.field_type == 'file':
                self.fields[field_name] = forms.FileField(
                    label=field.name,
                    required=field.required,
                    widget=forms.FileInput(attrs={'class': 'form-control'})
                )
            
            # Store field_id as widget attribute for later retrieval
            self.fields[field_name].widget.attrs['data-field-id'] = field.id
    
    def save(self):
        """Save form data to TaskOutput model"""
        saved_outputs = []
        
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('field_'):
                field_id = int(field_name.split('_')[1])
                output_field = TaskOutputField.objects.get(id=field_id)
                
                # Handle file uploads separately
                if output_field.field_type == 'file':
                    output, created = TaskOutput.objects.update_or_create(
                        output_field=output_field,
                        user=self.user,
                        defaults={'value_file': value}
                    )
                else:
                    # For checkbox, convert list to comma-separated string
                    if isinstance(value, list):
                        value = ', '.join(value)
                    
                    output, created = TaskOutput.objects.update_or_create(
                        output_field=output_field,
                        user=self.user,
                        defaults={'value_text': str(value)}
                    )
                
                saved_outputs.append(output)
        
        return saved_outputs
