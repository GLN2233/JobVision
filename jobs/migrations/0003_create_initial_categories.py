from django.db import migrations

def create_initial_categories(apps, schema_editor):
    JobCategory = apps.get_model('jobs', 'JobCategory')
    
    # 创建主要职位类别
    categories = [
        '技术',
        '产品',
        '设计',
        '运营',
        '市场',
        '销售',
        '人力资源',
        '行政',
        '财务',
        '法务',
    ]
    
    for category in categories:
        JobCategory.objects.create(name=category)

def delete_initial_categories(apps, schema_editor):
    JobCategory = apps.get_model('jobs', 'JobCategory')
    JobCategory.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('jobs', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_categories, delete_initial_categories),
    ] 