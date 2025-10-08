# tasks/forms.py

"""
Task forms with secure file upload handling.

Dynamically generates form fields based on TaskOutputField definitions
with comprehensive validation.
"""

from django import forms
from django.contrib.auth import get_user_model

from core.validators import validate_file_extension, validate_file_size
from organizations.models import Department
from .models import Task, TaskOutputField, TaskOutput

User = get_user_model()



class TaskForm(forms.ModelForm):
    """
    Form for creating and editing tasks with dynamic filtering.
    
    Filters departments and users based on selected organization.
    Uses AJAX for dynamic field population on organization selection.
    """

    class Meta:
        model = Task
        fields = [
            'name', 'description', 'organization', 'departments',
            'assigned_users', 'viewers', 'due_date'
        ]
        widgets = {
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'departments': forms.CheckboxSelectMultiple(),
            'assigned_users': forms.CheckboxSelectMultiple(),
            'viewers': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize form and filter choices based on organization.
        
        On initial load (create mode), sets empty querysets for dependent fields.
        On edit mode, loads data for the task's organization.
        On form submission with validation errors, maintains selected values.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)

        # Set CSS classes and attributes
        self.fields['organization'].widget.attrs.update({
            'required': True,
            'class': 'form-select'
        })
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs['class'] = 'form-control'

        # Filter related fields based on organization
        if self.instance.pk:
            # Edit mode - use existing organization
            self.fields['departments'].queryset = (
                self.instance.organization.departments.all()
            )
            self.fields['assigned_users'].queryset = User.objects.filter(
                user_org_roles__organization=self.instance.organization
            ).distinct()
            self.fields['viewers'].queryset = User.objects.filter(
                user_org_roles__organization=self.instance.organization
            ).distinct()
        elif 'organization' in self.data:
            # Form submission with validation errors - maintain selections
            try:
                org_id = int(self.data.get('organization'))
                self.fields['departments'].queryset = (
                    Department.objects.filter(organization_id=org_id)
                )
                self.fields['assigned_users'].queryset = User.objects.filter(
                    user_org_roles__organization_id=org_id
                ).distinct()
                self.fields['viewers'].queryset = User.objects.filter(
                    user_org_roles__organization_id=org_id
                ).distinct()
            except (ValueError, TypeError):
                # Invalid organization ID - set empty querysets
                self.fields['departments'].queryset = (
                    Department.objects.none()
                )
                self.fields['assigned_users'].queryset = User.objects.none()
                self.fields['viewers'].queryset = User.objects.none()
        else:
            # Initial load (create mode) - empty querysets
            # AJAX will populate these when organization is selected
            self.fields['departments'].queryset = Department.objects.none()
            self.fields['assigned_users'].queryset = User.objects.none()
            self.fields['viewers'].queryset = User.objects.none()


class TaskOutputForm(forms.ModelForm):
    """
    Form for creating and editing task outputs.
    
    Used for individual output field submissions.
    """

    class Meta:
        model = TaskOutput
        fields = ['output_field', 'value_text', 'value_file']


class TaskOutputFieldForm(forms.ModelForm):
    """
    Form for creating and editing task output fields.
    
    Defines the structure of data to be collected from task completion.
    """

    class Meta:
        model = TaskOutputField
        fields = [
            'task', 'name', 'field_type', 'required',
            'options', 'min_value', 'max_value'
        ]
        widgets = {
            'options': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Comma-separated options for radio/checkbox'
            }),
        }




class DynamicTaskCompletionForm(forms.Form):
    """
    Dynamically generates form fields based on TaskOutputField definitions.
    
    Includes secure file upload validation and supports multiple field types:
    - Text (textarea)
    - Radio buttons
    - Checkboxes
    - Yes/No
    - Numbers (with min/max validation)
    - File uploads (with extension and size validation)
    """

    def __init__(self, task, user, *args, **kwargs):
        """
        Initialize form with dynamic fields based on task output fields.

        Args:
            task: Task instance to generate fields for
            user: Current user instance completing the task
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.task = task
        self.user = user

        output_fields = task.output_fields.all()

        for field in output_fields:
            field_name = f'field_{field.id}'
            created_field = None

            if field.field_type == 'text':
                created_field = forms.CharField(
                    label=field.name,
                    required=field.required,
                    widget=forms.Textarea(attrs={
                        'rows': 4,
                        'class': 'form-control',
                        'placeholder': f'Enter {field.name.lower()}...'
                    })
                )

            elif field.field_type == 'radio':
                if field.options:
                    choices = [
                        (opt.strip(), opt.strip())
                        for opt in field.options.split(',')
                    ]
                    created_field = forms.ChoiceField(
                        label=field.name,
                        choices=choices,
                        widget=forms.RadioSelect(attrs={
                            'class': 'form-check-input'
                        }),
                        required=field.required
                    )

            elif field.field_type == 'checkbox':
                if field.options:
                    choices = [
                        (opt.strip(), opt.strip())
                        for opt in field.options.split(',')
                    ]
                    created_field = forms.MultipleChoiceField(
                        label=field.name,
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple(attrs={
                            'class': 'form-check-input'
                        }),
                        required=field.required
                    )

            elif field.field_type == 'yesno':
                created_field = forms.ChoiceField(
                    label=field.name,
                    choices=[('yes', 'Yes'), ('no', 'No')],
                    widget=forms.RadioSelect(attrs={
                        'class': 'form-check-input'
                    }),
                    required=field.required
                )

            elif field.field_type == 'number':
                created_field = forms.FloatField(
                    label=field.name,
                    required=field.required,
                    min_value=field.min_value,
                    max_value=field.max_value,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': 'any',
                        'placeholder': f'Enter {field.name.lower()}...'
                    })
                )
                if field.min_value is not None or field.max_value is not None:
                    help_parts = []
                    if field.min_value is not None:
                        help_parts.append(f"Minimum: {field.min_value}")
                    if field.max_value is not None:
                        help_parts.append(f"Maximum: {field.max_value}")
                    created_field.help_text = " | ".join(help_parts)

            elif field.field_type == 'file':
                created_field = forms.FileField(
                    label=field.name,
                    required=field.required,
                    validators=[
                        validate_file_extension,
                        validate_file_size,
                    ],
                    widget=forms.FileInput(attrs={
                        'class': 'form-control',
                        'accept': ','.join([
                            '.doc', '.docx', '.txt', '.pdf',
                            '.xls', '.xlsx', '.png', '.jpg',
                            '.jpeg', '.gif', '.zip', '.csv',
                            '.ppt', '.pptx'
                        ])
                    }),
                    help_text=(
                        'Max size: 10MB. Allowed: PDF, Word, Excel, '
                        'Images, ZIP, PPT'
                    )
                )

            if created_field:
                self.fields[field_name] = created_field
                self.fields[field_name].widget.attrs['data-field-id'] = (
                    field.id
                )

    def save(self):
        """
        Save form data to TaskOutput model.
        
        Creates or updates TaskOutput instances for each field.
        For file fields, stores the uploaded file securely.
        For other fields, stores the value as text.

        Returns:
            list: List of saved TaskOutput instances
        """
        saved_outputs = []

        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('field_'):
                field_id = int(field_name.split('_')[1])

                try:
                    output_field = TaskOutputField.objects.get(id=field_id)
                except TaskOutputField.DoesNotExist:
                    continue

                if output_field.field_type == 'file':
                    if value:  # Only update if file was uploaded
                        output, created = TaskOutput.objects.update_or_create(
                            output_field=output_field,
                            user=self.user,
                            defaults={'value_file': value}
                        )
                        saved_outputs.append(output)
                else:
                    # Convert list values (checkboxes) to comma-separated string
                    if isinstance(value, list):
                        value = ', '.join(value)

                    output, created = TaskOutput.objects.update_or_create(
                        output_field=output_field,
                        user=self.user,
                        defaults={'value_text': str(value)}
                    )
                    saved_outputs.append(output)

        return saved_outputs
