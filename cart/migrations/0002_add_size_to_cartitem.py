from django.db import migrations, models
import django.db.models.deletion

def set_default_size(apps, schema_editor):
    CartItem = apps.get_model('cart', 'CartItem')
    Size = apps.get_model('products', 'Size')
    # Get first available size or create a default one if none exists
    default_size = Size.objects.first()
    if not default_size:
        default_size = Size.objects.create(name='Default', is_active=True)
    
    for item in CartItem.objects.all():
        item.size = default_size
        item.save()

class Migration(migrations.Migration):
    # Use the last actual migration as dependency
    dependencies = [
        ('cart', '0001_initial'),  # This should match your first migration
        ('products', '0001_initial'),  # Or whatever your products initial migration is
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='size',
            field=models.ForeignKey(
                'products.Size',
                on_delete=django.db.models.deletion.CASCADE,
                null=True,  # Allow null temporarily
                blank=True
            ),
        ),
        migrations.RunPython(set_default_size),
        migrations.AlterField(
            model_name='cartitem',
            name='size',
            field=models.ForeignKey(
                'products.Size',
                on_delete=django.db.models.deletion.CASCADE,
                null=False  # Make non-nullable after data migration
            ),
        ),
    ]