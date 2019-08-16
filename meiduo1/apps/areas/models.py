from django.db import models

class Area(models.Model):
    name = models.CharField(max_length=20)
    parent = models.ForeignKey('self', related_name='subs', null=True)

    class Meta:
        db_table = 'tb_areas'
