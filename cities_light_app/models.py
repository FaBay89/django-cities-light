from django.db import models

from cities_light.abstract_models import (AbstractCity, AbstractRegion,
                                          AbstractCountry)
from cities_light.receivers import connect_default_signals


class Country(AbstractCountry):

    def get_name_for_lang(self, lang):
        name = get_name_for_lang(geoname_id=self.geoname_id, lang=lang)
        if not name:
            name = self.name
        return name

connect_default_signals(Country)


class Region(AbstractRegion):

    def get_name_for_lang(self, lang):
        name = get_name_for_lang(geoname_id=self.geoname_id, lang=lang)
        if not name:
            name = self.name
        return name

connect_default_signals(Region)


class City(AbstractCity):

    def get_name_for_lang(self, lang):
        name = get_name_for_lang(geoname_id=self.geoname_id, lang=lang)
        if not name:
            name = self.name
        return name

connect_default_signals(City)


class AlternateName(models.Model):
    geoname_id = models.IntegerField(db_index=True)

    name = models.CharField(max_length=200)

    language = models.CharField(max_length=10, blank=True)
    is_preferred = models.BooleanField(default=False)
    is_short = models.BooleanField(default=False)


def get_name_for_lang(geoname_id, lang):
    alt_names = AlternateName.objects.filter(geoname_id=geoname_id).filter(language__iexact=lang)
    preferred = alt_names.filter(is_preferred=True)
    if preferred:
        return preferred.first().name
    elif alt_names:
        return alt_names.first().name
    else:
        return None
