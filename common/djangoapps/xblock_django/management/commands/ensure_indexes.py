from django.core.management.base import BaseCommand

from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore



class Command(BaseCommand):

    args = ''
    help = 'Creates the indexes for ContentStore and ModuleStore databases'

    def handle(self, *args, **options):
        contentstore().ensure_indexes()
        modulestore().ensure_indexes()
        print('contentstore and modulestore indexes created!')
