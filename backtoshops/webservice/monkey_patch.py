from django.db.backends.postgresql_psycopg2.base import DatabaseOperations, DatabaseWrapper

def lookup_cast(self, lookup_type):
      if lookup_type in('icontains', 'istartswith'):
          return "UPPER(unaccent(%s::text))"
      else:
          return super(DatabaseOperations, self).lookup_cast(lookup_type)

def patch_unaccent():
    DatabaseOperations.lookup_cast = lookup_cast
    DatabaseWrapper.operators['icontains'] = 'LIKE UPPER(unaccent(%s))'
    DatabaseWrapper.operators['istartswith'] = 'LIKE UPPER(unaccent(%s))'
