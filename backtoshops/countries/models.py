#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Country(models.Model):
    """
    International Organization for Standardization (ISO) 3166-1 Country list

     * ``iso`` = ISO 3166-1 alpha-2
     * ``name`` = Official country names used by the ISO 3166/MA in capital letters
     * ``printable_name`` = Printable country names for in-text use
     * ``iso3`` = ISO 3166-1 alpha-3
     * ``numcode`` = ISO 3166-1 numeric

    Note::
        This model is fixed to the database table 'country' to be more general.
        Change ``db_table`` if this cause conflicts with your database layout.
        Or comment out the line for default django behaviour.

    """
    iso = models.CharField(_('ISO alpha-2'), max_length=2, primary_key=True)
    name = models.CharField(_('Official name (CAPS)'), max_length=128)
    printable_name = models.CharField(_('Country name'), max_length=128)
    iso3 = models.CharField(_('ISO alpha-3'), max_length=3, null=True)
    numcode = models.PositiveSmallIntegerField(_('ISO numeric'), null=True)

    class Meta:
        db_table = 'country'
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('name',)

    class Admin:
        list_display = ('printable_name', 'iso',)

    def __unicode__(self):
        return self.printable_name


class UsState(models.Model):
    """
    United States Postal Service (USPS) State Abbreviations

    Note::
        This model is fixed to the database table 'usstate' to be more general.
        Change ``db_table`` if this cause conflicts with your database layout.
        Or comment out the line for default django behaviour.

    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(_('State name'), max_length=50)
    abbrev = models.CharField(_('Abbreviation'), max_length=2)

    class Meta:
        db_table = 'usstate'
        verbose_name = _('US State')
        verbose_name_plural = _('US States')
        ordering = ('name',)

    class Admin:
        list_display = ('name', 'abbrev',)

    def __unicode__(self):
        return self.name


class CaProvince(models.Model):
    """
    Provinces and territories of Canada.
    """
    name = models.CharField(max_length=50)
    abbrev = models.CharField(max_length=2)

    class Meta:
        db_table = 'ca_province'
        verbose_name = _('CA Provinces and Territories')
        verbose_name_plural = _('CA Provinces and Territories')
        ordering = ('name',)

    class Admin:
        list_display = ('name', 'abbrev',)

    def __unicode__(self):
        return self.name

class CnProvince(models.Model):
    """
    Provinces and territories of China.
    """
    name = models.CharField(max_length=50)
    abbrev = models.CharField(max_length=2)

    class Meta:
        db_table = 'cn_province'
        verbose_name = _('CN Provinces and Territories')
        verbose_name_plural = _('CN Provinces and Territories')
        ordering = ('name',)

    class Admin:
        list_display = ('name', 'abbrev',)

    def __unicode__(self):
        return self.name

class CountryXCurrency(models.Model):
    """
    Country & Currency Mapping Table
    """
    country = models.ForeignKey('Country')
    currency = models.CharField(max_length=3)

    class Meta:
        db_table = 'country_x_currency'
        verbose_name = _('Country & Currency Mapping')
        verbose_name_plural = _('Country & Currency Mapping')
        ordering = ('country',)
        unique_together = (("country", "currency"),)

    class Admin:
        list_display = ('country', 'currency',)

    def __unicode__(self):
        return self.name

