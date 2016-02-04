"""
Signals for cities_light:

    city_items_pre_import / region_items_pre_import / country_items_pre_import /
    translation_items_pre_import # Note: Be careful because of long runtime; it will be called VERY often.

        Emited by city_import() in the cities_light command for each row parsed in
        the data file. If a signal reciever raises InvalidItems then it will be
        skipped.
        An example is worth 1000 words: if you want to import only cities from
        France, USA and Belgium you could do as such::
            import cities_light
            def filter_city_import(sender, items, **kwargs):
                if items[8] not in ('FR', 'US', 'BE'):
                    raise cities_light.InvalidItems()
            cities_light.signals.city_items_pre_import.connect(filter_city_import)
        Note: this signal gets a list rather than a City instance for performance
        reasons.

    city_items_post_import / region_items_post_import / country_items_post_import

        Emited by city_import() in the cities_light command for each row parsed in
        the data file, right before saving City object. Along with City instance
        it pass items with geonames data. Will be useful, if you define custom
        cities models with ``settings.CITIES_LIGHT_APP_NAME``.
        Example::
            import cities_light
            def process_city_import(sender, instance, items, **kwargs):
                instance.timezone = items[ICity.timezone]
            cities_light.signals.city_items_post_import.connect(process_city_import)
"""
from django.utils.encoding import force_text

import cities_light
from cities_light.settings import ICountry, IRegion, ICity, IAlternate, TRANSLATION_LANGUAGES
from cities_light import signals
from ..models import Country, Region, City, AlternateName

from django.dispatch import receiver


@receiver(signals.city_items_pre_import)
def city_population_filter(sender, items, **kwargs):
    if int(items[ICity.population]) < 30000:
        raise cities_light.InvalidItems()


@receiver(signals.translation_items_pre_import)
def import_alternate_names(sender, items, **kwargs):

        if len(items) > 6:
            # avoid colloquial, and historic, but dont avoid shortnames.
            # often are the shortnames the preferred ones (Germany vs. Federal Republic of Germany)
            raise cities_light.InvalidItems()

        item_lang = items[IAlternate.language]

        if item_lang not in TRANSLATION_LANGUAGES:
            raise cities_light.InvalidItems()

        item_geoid = items[IAlternate.geonameid]
        item_name = items[IAlternate.name]

        # arg optimisation code kills me !!!
        item_geoid = int(item_geoid)

        if item_geoid in sender.country_ids:
            model_class = Country
        elif item_geoid in sender.region_ids:
            model_class = Region
        elif item_geoid in sender.city_ids:
            model_class = City
        else:
            raise cities_light.InvalidItems()

        #########
        # translation_data for further processing in cities_light
        # (generate alternate_names and search_names field)
        if item_geoid not in sender.translation_data[model_class]:
            sender.translation_data[model_class][item_geoid] = {}

        if item_lang not in sender.translation_data[model_class][item_geoid]:
            sender.translation_data[model_class][item_geoid][item_lang] = []

        sender.translation_data[model_class][item_geoid][item_lang].append(
            item_name)
        ########

        try:
            is_preferred = (items[IAlternate.isPreferred] == '1')
        except IndexError:
            is_preferred = False
        try:
            is_short = (items[IAlternate.isShort] == '1')
        except IndexError:
            is_short = False

        try:
            model = model_class.objects.get(geoname_id=item_geoid)
        except model_class.DoesNotExist:
            raise cities_light.InvalidItems()

        lang = force_text(item_lang)
        name = force_text(item_name)

        try:
            alt_obj = AlternateName.objects.get(name=name, language=lang, geoname_id=item_geoid)
            if alt_obj.is_preferred != is_preferred or alt_obj.is_short != is_short:
                alt_obj.is_preferred = is_preferred
                alt_obj.is_short = is_short
                alt_obj.save()
        except AlternateName.DoesNotExist:

            if name == model.name and not is_preferred:
                raise cities_light.InvalidItems()

            alt_obj = AlternateName(geoname_id=item_geoid,
                                    language=lang,
                                    name=name,
                                    is_preferred=is_preferred,
                                    is_short=is_short,
                                    )
            alt_obj.save()

        raise cities_light.InvalidItems() # Rest der umgebenden Funktion wurde hier erledigt (s. translation_data)

